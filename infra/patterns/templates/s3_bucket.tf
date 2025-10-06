// infra/patterns/templates/s3_bucket.tf
variable "bucket_name"   { type = string }
variable "force_destroy" { type = bool   default = false }
variable "block_public"  { type = bool   default = true }

resource "aws_s3_bucket" "this" {
  bucket        = var.bucket_name
  force_destroy = var.force_destroy
  tags          = var.tags
}

resource "aws_s3_bucket_public_access_block" "block" {
  count                   = var.block_public ? 1 : 0
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_name" { value = aws_s3_bucket.this.bucket }
output "bucket_arn"  { value = aws_s3_bucket.this.arn    }
