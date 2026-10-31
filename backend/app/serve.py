"""Hosted entry point with provider-supplied PORT; no development reloader."""
import os
import uvicorn


def main():
    try:
        port = int(os.getenv('PORT', '8000'))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError as exc:
        raise RuntimeError('PORT must be an integer from 1 to 65535.') from exc
    uvicorn.run('app.production:create_app', factory=True, host='0.0.0.0', port=port,
                forwarded_allow_ips=os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1'))


if __name__ == '__main__':
    main()
