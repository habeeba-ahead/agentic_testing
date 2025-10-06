// infra/patterns/templates/s3_notification_lambda.tf
# Generic S3 → Lambda trigger
variable "bucket_id"    { type = string } # aws_s3_bucket.this.id
variable "function_arn" { type = string }
variable "events"       { type = list(string) default = ["s3:ObjectCreated:*"] }
variable "prefix"       { type = string      default = null }
variable "suffix"       { type = string      default = null }

resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowInvokeFromS3"
  action        = "lambda:InvokeFunction"
  function_name = var.function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.bucket_id}"
}

resource "aws_s3_bucket_notification" "notify" {
  bucket = var.bucket_id

  lambda_function {
    lambda_function_arn = var.function_arn
    events              = var.events
    filter_prefix       = var.prefix
    filter_suffix       = var.suffix
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}
