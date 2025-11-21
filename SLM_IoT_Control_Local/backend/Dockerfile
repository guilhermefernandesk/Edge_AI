FROM python:3.11-slim

# define diretório de trabalho
WORKDIR /usr/src/app

# copia dependências
COPY requirements.txt .

# instala dependências
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

# copia o projeto
COPY . .

# expõe a porta do flask
EXPOSE 5000

# comando padrão
CMD ["python", "server.py"]