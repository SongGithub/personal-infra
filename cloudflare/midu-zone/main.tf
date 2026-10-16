# Provider v5 schema: https://github.com/cloudflare/terraform-provider-cloudflare/tree/v5.28.0/docs/resources
resource "cloudflare_zone" "midu" {
  account = { id = var.account_id }
  name    = "midu.com.au"
  type    = "full"
  paused  = false

  lifecycle {
    prevent_destroy = true
  }
}
