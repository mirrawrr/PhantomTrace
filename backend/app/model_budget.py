"""Conservative USD reservations for the hosted Spark/Voice demo only.

Pricing checked 2026-11-01: Spark $1.25/M input, $4.25/M output;
Voice $0.18/hour. No cached-input discount is assumed. No SDK retries.
Not an account-wide billing limit. Ledger must be on persistent storage.
"""
from contextlib import closing
import os
import sqlite3
import tempfile
from decimal import Decimal, ROUND_CEILING


class DemoBudgetError(RuntimeError):
    pass


def ledger():
    db = sqlite3.connect(os.getenv('DEMO_USAGE_DB', os.path.join(tempfile.gettempdir(), 'phantomtrace-usage.sqlite3')), timeout=5)
    db.execute('CREATE TABLE IF NOT EXISTS spend (id INTEGER PRIMARY KEY, micros INTEGER NOT NULL)')
    return db


def reserve(micros):
    try:
        ceiling = int(Decimal(os.getenv('DEMO_BUDGET_USD', '5')) * 1_000_000)
        if ceiling <= 0:
            raise ValueError()
        with closing(ledger()) as db:
            db.execute('BEGIN IMMEDIATE')
            used = db.execute('SELECT COALESCE(SUM(micros), 0) FROM spend').fetchone()[0]
            if used + micros > ceiling:
                raise DemoBudgetError('Live model budget exhausted; use recorded replay.')
            reservation_id = db.execute('INSERT INTO spend(micros) VALUES (?)', (micros,)).lastrowid
            db.commit()
            return reservation_id
    except (sqlite3.Error, ValueError, ArithmeticError) as exc:
        raise DemoBudgetError('Live model budget unavailable; use recorded replay.') from exc


class BudgetedResponses:
    def __init__(self, responses):
        self.responses = responses

    def create(self, **kwargs):
        # Reserve the entire 1,048,576 context at uncached input pricing,
        # plus output. Only these models/tools and bounded outputs are allowed.
        if kwargs.get('model') != 'muse-spark-1.3' or not 1 <= kwargs.get('max_output_tokens', 0) <= 6500:
            raise DemoBudgetError('Hosted budget supports bounded Muse Spark 1.3 requests only.')
        if any(tool.get('type') != 'function' for tool in kwargs.get('tools', [])):
            raise DemoBudgetError('Hosted budget does not allow additional billed tools.')
        reservation = 1_400_000  # $1.40; worst case $1.3384 per request
        reservation_id = reserve(reservation)
        result = self.responses.create(**kwargs)
        usage = getattr(result, 'usage', None)
        inputs, outputs = getattr(usage, 'input_tokens', None), getattr(usage, 'output_tokens', None)
        if (isinstance(inputs, int) and isinstance(outputs, int)
                and 0 <= inputs <= 1048576 and 0 <= outputs <= 6500):
            charge = int((Decimal(inputs) * Decimal('1.25') + Decimal(outputs) * Decimal('4.25')).to_integral_value(rounding=ROUND_CEILING))
            try:
                with closing(ledger()) as db:
                    db.execute('UPDATE spend SET micros=? WHERE id=?', (charge, reservation_id))
                    db.commit()
            except sqlite3.Error:
                pass  # Retain the larger reservation if reconciliation fails.
        return result
