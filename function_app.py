"""
@author Tom Butler
@date 2025-10-25
@description Azure Function App for scheduled news processing.
             Runs batch processor on a timer trigger for automated daily execution.
"""

import logging
import azure.functions as func
from batch_processor import BatchProcessor

app = func.FunctionApp()


@app.timer_trigger(
    schedule="0 0 6 * * *",  # Daily at 6 AM UTC
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True
)
def scheduled_batch_processor(timer: func.TimerRequest) -> None:
    """
    Azure Function triggered daily to process news articles.
    @param {func.TimerRequest} timer - Timer trigger information
    """
    logging.info("Scheduled batch processor triggered")

    if timer.past_due:
        logging.warning("Timer trigger is past due")

    try:
        processor = BatchProcessor()
        processor.run_batch_processing()
        logging.info("Batch processing completed successfully")
    except Exception as e:
        logging.error(f"Batch processing failed: {str(e)}")
        raise


@app.function_name(name="ManualBatchProcessor")
@app.route(route="process", auth_level=func.AuthLevel.FUNCTION)
def manual_batch_processor(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP-triggered function for manual batch processing execution.
    @param {func.HttpRequest} req - HTTP request object
    @return {func.HttpResponse} HTTP response with processing status
    """
    logging.info("Manual batch processor triggered via HTTP")

    try:
        # Check for article count parameter
        article_count = req.params.get('articles')
        if article_count:
            try:
                article_count = int(article_count)
                logging.info(f"Processing {article_count} articles (manual override)")
            except ValueError:
                return func.HttpResponse(
                    "Invalid 'articles' parameter. Must be an integer.",
                    status_code=400
                )

        processor = BatchProcessor()

        # Override article count if provided
        if article_count:
            processor.TOTAL_ARTICLES = article_count

        processor.run_batch_processing()

        logging.info("Manual batch processing completed successfully")

        return func.HttpResponse(
            "Batch processing completed successfully",
            status_code=200
        )

    except Exception as e:
        error_msg = f"Batch processing failed: {str(e)}"
        logging.error(error_msg)

        return func.HttpResponse(
            error_msg,
            status_code=500
        )


@app.function_name(name="HealthCheck")
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for monitoring.
    @param {func.HttpRequest} req - HTTP request object
    @return {func.HttpResponse} Health status response
    """
    logging.info("Health check requested")

    return func.HttpResponse(
        '{"status": "healthy", "service": "NewsPerspective Function App"}',
        status_code=200,
        mimetype="application/json"
    )
