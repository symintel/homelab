resource "incus_cluster_group" "x86_nodes" {
  name        = "x86-nodes"
  description = "M920q (invincible) + M700 (oliver)"
}

resource "incus_cluster_group" "arm64_nodes" {
  name        = "arm64-nodes"
  description = "Orange Pi 5 Plus (deborah)"
}
