"""Completed tool executions as SSE. Never streams private model reasoning."""
import json
import asyncio
from time import monotonic
from queue import SimpleQueue
from threading import Thread

from fastapi.responses import StreamingResponse
from openai import OpenAIError

from app.model_budget import DemoBudgetError
from app.services.adaptive_agent import investigate_adaptive, AdaptiveFailure, EvidenceWorkspace
from app.services.investigation_agent import InvalidLogs
from app.services.testimony import check_testimony, TestimonyFailure


def investigation_events(request, *, investigator=investigate_adaptive):
    queue = SimpleQueue()
    def emit(kind, data):
        queue.put((kind, data))

    def work():
        try:
            result = investigator(request, on_event=emit)
            if request.witness_statement.strip():
                try:
                    result['testimony'] = check_testimony(request.witness_statement, EvidenceWorkspace(request))
                except TestimonyFailure as exc:
                    result['testimony_error_code'] = exc.code
                    result['testimony_error'] = 'Witness check did not finish (' + exc.code + '); testimony remains unverified.'
            emit('result', result)
        except InvalidLogs:
            emit('error', {'code': 'invalid_logs', 'message': 'Check log format and timestamps.'})
        except DemoBudgetError:
            emit('error', {'code': 'budget_unavailable', 'message': 'Live model budget unavailable or exhausted. Use recorded replay.'})
        except AdaptiveFailure as exc:
            emit('error', {'code': exc.code, 'provider': exc.diagnostics.get('provider', {}),
                           'message': 'Investigation did not finish. Completed tool activity is retained; no final verdict is available.'})
        except (OpenAIError, RuntimeError, ValueError):
            emit('error', {'code': 'investigation_failed', 'message': 'Investigation did not finish. Check configuration or retry.'})
        except Exception:
            # Do not expose source values, provider bodies, or tracebacks over SSE.
            emit('error', {'code': 'investigation_failed', 'message': 'Investigation did not finish.'})
        finally:
            queue.put(None)

    Thread(target=work, daemon=True).start()
    while True:
        item = queue.get()
        if item is None:
            break
        kind, data = item
        yield 'event: ' + kind + '\ndata: ' + json.dumps(data) + '\n\n'


def stream_investigation(request):
    return StreamingResponse(investigation_events(request), media_type='text/event-stream',
        headers={'Cache-Control': 'no-store, no-transform', 'X-Accel-Buffering': 'no'})


async def connection_pings():
    """Real server-clock diagnostics only. No evidence, model or tool execution."""
    start = monotonic()
    for index in range(1, 4):
        if index > 1:
            await asyncio.sleep(1)
        yield 'event: ping\ndata: ' + json.dumps({
            'index': index, 'elapsed_ms': round((monotonic() - start) * 1000),
            'scope': 'Connection test only; no model calls.'}) + '\n\n'
