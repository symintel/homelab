terraform {
  required_providers {
    incus = {
      source  = "lxc/incus"
      version = "~> 0.1"
    }
  }
}

provider "incus" {
  remote {
    name    = "homelab"
    address = var.incus_remote_address
  }
}
