FROM python:3.11-slim

WORKDIR / app
  
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn" , "-W","4","-B" "0.0.0.0:8080", "app.py"]
