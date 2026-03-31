# =========================
# BASE IMAGE
# =========================
FROM python:3.11

# =========================
# WORK DIRECTORY
# =========================
WORKDIR /app

# =========================
# COPY FILES
# =========================
COPY . .

# =========================
# INSTALL DEPENDENCIES
# =========================
RUN pip install --no-cache-dir fastapi uvicorn openai
# =========================
# EXPOSE PORT
# =========================
EXPOSE 8000

# =========================
# RUN APP
# =========================
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]