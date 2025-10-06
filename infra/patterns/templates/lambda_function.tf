// infra/patterns/templates/lambda_function.tf
variable "function_name"     { type = string }
variable "runtime"           { type = string  default = "python3.11" }
variable "handler"           { type = string }             # e.g., "src/orders/handlers.create_order"
variable "role_arn"          { type = string  default = null }
variable "memory_mb"         { type = number  default = 512 }
variable "timeout_seconds"   { type = number  default = 15 }
variable "env"               { type = map(string) default = {} }
variable "zip_s3_bucket"     { type = string  default = null } # one of (zip_s3_*) OR (filename)
variable "zip_s3_key"        { type = string  default = null }
variable "filename"          { type = string  default = null } # used by stitch-time packaging

resource "aws_iam_role" "lambda_exec" {
  count = var.role_arn == null ? 1 : 0
  name  = "${var.function_name}-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "logs" {
  count      = var.role_arn == null ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

locals {
  effective_role_arn = var.role_arn != null ? var.role_arn : aws_iam_role.lambda_exec[0].arn
}

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = local.effective_role_arn
  runtime       = var.runtime
  handler       = var.handler
  timeout       = var.timeout_seconds
  memory_size   = var.memory_mb

  dynamic "environment" {
    for_each = length(var.env) > 0 ? [1] : []
    content { variables = var.env }
  }

  # Flexible code source (stitch agent decides which path to use)
  dynamic "s3_bucket" { for_each = var.zip_s3_bucket == null ? [] : [var.zip_s3_bucket] content {} }
  dynamic "s3_key"    { for_each = var.zip_s3_key    == null ? [] : [var.zip_s3_key]    content {} }
  filename = var.filename

  tags = var.tags
}

output "function_name" { value = aws_lambda_function.this.function_name }
output "function_arn"  { value = aws_lambda_function.this.arn }
