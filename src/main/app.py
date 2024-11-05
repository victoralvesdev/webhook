from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Settings
from database.mongo.connection import init_db
from models.user import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="KirvanoWebhook",
    description="Gera um login após a venda do serviço",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return JSONResponse({"status": "success", "message": "GET recebido com sucesso."})


@app.post("/")
async def webhook(request: Request):
    data = await request.json()

    if data.get("event") != "SALE_APPROVED":
        raise HTTPException(status_code=400, detail="Evento ou dados inválidos.")

    customer_email = data.get("customer", {}).get("email")
    customer_name = data.get("customer", {}).get("name")
    product_name = data.get("products", [{}])[0].get("name", "Produto não especificado")
    payment_method = data.get("payment", {}).get("method", "Método não especificado")
    total_price = data.get("total_price", "Valor não especificado")

    if not customer_email or not customer_name:
        raise HTTPException(status_code=400, detail="Dados essenciais estão faltando.")

    existing_user = await User.find_one({"email": customer_email})  # type: ignore
    if existing_user:
        return HTTPException(status_code=200, detail="E-mail já registrado.")

    await User.insert_one(User(username=customer_name, email=customer_email))
    user = await User.find_one({"email": customer_email})  # type: ignore

    if user:
        email_body = f"""
        <html><head><style>
        body {{ font-family: Arial; color: #333; }}
        .c {{ max-width: 600px; margin: 0 auto; }}
        .h {{ background: #f8f9fa; padding: 20px; text-align: center; }}
        .ct {{ padding: 20px; background: #fff; border: 1px solid #e9ecef; }}
        .ft {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        .pd {{ font-weight: bold; color: #007bff; }}
        .if {{ margin: 10px 0; }}
        </style></head><body><div class='c'>
        <div class='h'><h2>Compra Aprovada!</h2></div>
        <div class='ct'><p>Olá, <strong>{customer_name}</strong>,</p><p>Detalhes da compra:</p>
        <div class='if'><strong>Produto:</strong> <span class='pd'>{product_name}</span></div>
        <div class='if'><strong>Meio de Pagamento:</strong> {payment_method}</div>
        <div class='if'><strong>Valor Total:</strong> {total_price}</div>
        <div class='if'><strong>E-mail:</strong> {customer_email}</div>
        <div class='if'><strong>Senha de Acesso:</strong> {user.password}</div> 
        <p>Use os dados acima para acessar seu produto.</p></div>
        <div class='ft'><p>Obrigado por comprar conosco!</p></div></div></body></html>
        """

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Compra Aprovada - Detalhes da sua compra"
            msg["From"] = Settings.SMTP_FROM_NAME
            msg["To"] = customer_email
            msg.attach(MIMEText(email_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=Settings.SMTP_HOST,
                port=Settings.SMTP_PORT,
                username=Settings.SMTP_USER,
                password=Settings.SMTP_PASS,
                use_tls=True,
            )

            return JSONResponse(
                {"status": "success", "message": "E-mail enviado com sucesso."},
                status_code=200,
            )

        except Exception as email_error:
            print(f"Erro ao enviar e-mail: {email_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao enviar e-mail: {email_error} | Email do usuário: {customer_email}",
            )
    else:
        return HTTPException(status_code=500, detail="Ocorreu um erro interno.")
