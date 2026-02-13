FROM python:3.9

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements and install
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy all your files (including faiss_index and html)
COPY --chown=user . /app

# Expose the port
EXPOSE 7860

# CMD to start the app. 
# IMPORTANT: "main:app" tells it to look in main.py for the 'app' object
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]