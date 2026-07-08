# app/features/ussd/services.py

from fastapi.responses import PlainTextResponse


class USSDService:

    async def handle(
        self,
        sessionId: str,
        serviceCode: str,
        phoneNumber: str,
        text: str,
    ):

        if text == "":
            return PlainTextResponse(
                self.main_menu(),
                media_type="text/plain",
            )

        values = text.split("*")

        if values[0] == "1":
            return PlainTextResponse(
                self.register_menu(values),
                media_type="text/plain",
            )

        elif values[0] == "2":

            return PlainTextResponse(
                "END Login coming soon",
                media_type="text/plain",
            )

        return PlainTextResponse(
            "END Invalid Option",
            media_type="text/plain",
        )

    def main_menu(self):

        return (
            "CON Welcome to SokoSure\n"
            "1. Register\n"
            "2. Login"
        )

    def register_menu(self, values):

        if len(values) == 1:
            return "CON Enter National ID"

        if len(values) == 2:
            return "CON Enter Full Name"

        if len(values) == 3:
            return "CON Create 4-digit PIN"

        if len(values) == 4:
            return "CON Confirm PIN"

        if len(values) == 5:
            return "CON Select County"

        if len(values) == 6:
            return (
                "CON Business Type\n"
                "1. Clothes\n"
                "2. Vegetables\n"
                "3. Shoes\n"
                "4. Electronics\n"
                "5. Other"
            )

        if len(values) == 7:
            return (
                "CON Average Daily Income\n"
                "1. Below 500\n"
                "2. 500-1000\n"
                "3. 1000-3000\n"
                "4. Above 3000"
            )

        if len(values) == 8:
            return (
                "CON Payment Frequency\n"
                "1. Daily\n"
                "2. Weekly\n"
                "3. Monthly"
            )

        return (
            "END Registration complete.\n"
            "You'll receive an SMS shortly."
        )