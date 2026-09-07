"""Pure analysis core: turns Frames of Landmarks into Phase, Rep and Summary events.

Nothing in this package may import FastAPI, Starlette or ``pushform.app``/
``pushform.api``. The dependency runs one way only: the API imports analysis so
that the same code serves the live WebSocket, the tests and the replay CLI
(ADR-0002).
"""
