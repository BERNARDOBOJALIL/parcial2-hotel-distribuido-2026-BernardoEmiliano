"""Tests para availability-service — funciones puras sin RabbitMQ ni BD."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

def make_booking(check_in: str, check_out: str) -> MagicMock:
    b = MagicMock()
    b.check_in = date.fromisoformat(check_in)
    b.check_out = date.fromisoformat(check_out)
    return b
def overlaps(existing_check_in: date, existing_check_out: date,
             new_check_in: date, new_check_out: date) -> bool:
    #Devuelve True si los dos rangos se solapan
    return existing_check_in < new_check_out and existing_check_out > new_check_in

class TestOverlapLogic:

    def test_sin_solapamiento_consecutivo(self):
        #Reserva del 1-10, nueva del 10-15
        assert not overlaps(
            date(2024, 6, 1), date(2024, 6, 10),
            date(2024, 6, 10), date(2024, 6, 15),
        )

    def test_solapamiento_parcial_inicio(self):
        #Reserva del 1-10, nueva del 5-15
        assert overlaps(
            date(2024, 6, 1), date(2024, 6, 10),
            date(2024, 6, 5), date(2024, 6, 15),
        )

    def test_solapamiento_parcial_fin(self):
        #Reserva del 5-15, nueva del 1-10
        assert overlaps(
            date(2024, 6, 5), date(2024, 6, 15),
            date(2024, 6, 1), date(2024, 6, 10),
        )

    def test_solapamiento_contenido(self):
        #Reserva del 1-20, nueva del 5-10
        assert overlaps(
            date(2024, 6, 1), date(2024, 6, 20),
            date(2024, 6, 5), date(2024, 6, 10),
        )

    def test_mismo_rango_exacto(self):
        #Mismas fechas exactas
        assert overlaps(
            date(2024, 6, 1), date(2024, 6, 10),
            date(2024, 6, 1), date(2024, 6, 10),
        )

    def test_sin_solapamiento_antes(self):
        #Reserva del 10-20, nueva del 1-5
        assert not overlaps(
            date(2024, 6, 10), date(2024, 6, 20),
            date(2024, 6, 1), date(2024, 6, 5),
        )
class TestCancellationCompensation:

    def _make_session_mock(self, booking=None):
        #Devuelve un mock de SessionLocal que simula encontrar (o no) una reserva
        session = MagicMock()
        query_chain = session.query.return_value.filter.return_value
        query_chain.first.return_value = booking

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=session)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    def test_cancela_reserva_confirmada(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
        booking = MagicMock()
        booking.status = "CONFIRMED"
        booking.booking_id = "B001"
 
        session_ctx = self._make_session_mock(booking)
 
        import app.main as main_module
        with patch.object(main_module, "SessionLocal", return_value=session_ctx):
            result = main_module.apply_cancellation_compensation({"booking_id": "B001"})
 
        assert result is True
        assert booking.status == "CANCELLED"
 
    def test_no_encuentra_reserva(self):
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
        session_ctx = self._make_session_mock(booking=None)
 
        import app.main as main_module
        with patch.object(main_module, "SessionLocal", return_value=session_ctx):
            result = main_module.apply_cancellation_compensation({"booking_id": "B999"})
 
        assert result is False