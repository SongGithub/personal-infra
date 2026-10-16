mock_provider "cloudflare" {}
override_resource {
  target = cloudflare_zone.midu
}
run "preserve_shared_zone" {
  command = plan
  assert {
    condition     = cloudflare_zone.midu.name == "midu.com.au" && cloudflare_zone.midu.type == "full" && !cloudflare_zone.midu.paused
    error_message = "Preserve the active shared full zone; project stacks own DNS records."
  }
}
