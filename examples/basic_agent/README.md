# Basic agent metrics demo

1. Create a virtualenv and install the local package:

   ```bash
   pip install -e ../../packages/langgraph-telemetry
   ```

2. Run the loop (exposes Prometheus metrics on port **9100**):

   ```bash
   python main.py
   ```

3. From the repo root, start Prometheus (scrapes `host.docker.internal:9100`):

   ```bash
   docker compose up -d
   ```

4. Optional: run the Next.js dashboard (`PROMETHEUS_URL=http://127.0.0.1:9090 npm run dev` in `dashboard/`).
