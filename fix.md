 coderabbitai bot 9 minutes ago
⚠️ Potential issue | 🟠 Major

Add HTTP timeouts for NewsAPI and Azure Search indexing.

Prevent stalled runs and easier failure recovery.

-                response = requests.get(url)
+                response = requests.get(url, timeout=30)
@@
-            response = requests.post(
+            response = requests.post(
                 self.search_url,
                 headers=self.search_headers,
-                json={"value": docs}
+                json={"value": docs},
+                timeout=30
             )
Also applies to: 314-329

🧰 Tools


2. 
In run.py around lines 65-66, the call to requests.get(news_url) has no timeout
which can cause unbounded hangs; update the call to include a reasonable timeout
(e.g., timeout=10 or timeout=(3,10)) and wrap the request in a try/except that
catches requests.exceptions.Timeout and requests.exceptions.RequestException to
handle timeouts and other network errors (log the error and return/fail
gracefully).


3. 
In run.py around lines 67 to 73, the handler for HTTP 429 currently hardcodes a
60s wait; change it to honor the server-provided Retry-After header: read
response.headers.get('Retry-After'), if it's numeric parse seconds and use that,
otherwise try to parse an HTTP-date and compute seconds until that date,
fallback to a safe default (e.g., 60s) if parsing fails, optionally clamp to a
reasonable max wait, log the chosen wait value in the warning, call
time.sleep(wait_seconds) and then continue.


4. In run.py around lines 275 to 281, the code assumes result.choices[0] always
exists which can raise an IndexError if the API returns no choices; guard by
checking that result and result.choices are not None and that
len(result.choices) > 0 before accessing index 0, and if empty handle gracefully
(e.g., log an error/warning, raise a descriptive exception, or set rewritten to
a safe default and continue) so the code never directly indexes into an empty
choices list.

5. In run.py around lines 352 to 356, the requests.post call to Azure Search can
hang indefinitely; add a timeout argument (e.g. timeout=30) to the requests.post
call and wrap the call in a try/except that catches requests.Timeout and
requests.RequestException to log the error and fail gracefully (or retry if
desired). Ensure the timeout value is configurable via a constant or env var and
that the except block handles cleanup/reporting the failure instead of letting
the process hang.

6.
In run.py around lines 358 to 366, the current logic treats any 200/201 response
as a full success and only uses the HTTP status, but Azure Search returns
per-document indexing results; update the handling to parse response.json() and
inspect per-item statuses (e.g., the "value" array with status or error fields),
count how many documents succeeded vs failed, increment stats.uploads_successful
and stats.uploads_failed accordingly, and log summary plus any item-level errors
(IDs and error messages) for troubleshooting instead of relying solely on
response.status_code/response.text.

7. In search.py around lines 32-41 (and also apply same changes to lines 43-44),
the test_connection function makes a requests.get without a timeout and lacks
exception handling; update it to call requests.get with a sensible timeout
(e.g., timeout=5) and wrap the request in a try/except block to catch
requests.exceptions.RequestException, returning False and printing/logging a
clear error message on exception or non-200 status; ensure the function always
returns a boolean (True on 200, False otherwise) and include the response status
or exception details in the output.

