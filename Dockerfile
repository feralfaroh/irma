# Usa la imagen base oficial de Azure Functions para Python (Python 3.12)
FROM mcr.microsoft.com/azure-functions/python:4-python3.12

# Actualiza los repositorios e instala Chromium
RUN apt-get update && \
    apt-get install -y chromium && \
    rm -rf /var/lib/apt/lists/*

# Define la variable de entorno para que Selenium encuentre el binario de Chromium
ENV CHROME_BIN=/usr/bin/chromium

# Copia el binario de chromedriver que está en la raíz del proyecto al directorio /usr/local/bin del contenedor
COPY chromedriver /usr/local/bin/chromedriver

# Otorga permisos de ejecución al binario copiado
RUN chmod +x /usr/local/bin/chromedriver

# Copia todo el contenido de tu proyecto en el contenedor
COPY . /home/site/wwwroot

# (Opcional) Expone el puerto 80, que es el puerto interno de la Function App
EXPOSE 80

COPY requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt