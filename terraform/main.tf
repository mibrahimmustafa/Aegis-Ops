# Terraform Configuration for Aegis-Ops Infrastructure
# This module provisions an Azure Kubernetes Service (AKS) cluster as the foundation for the self-healing ecosystem.

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "aegis_rg" {
  name     = "rg-aegis-ops-prod"
  location = "East US"
}

# Virtual Network
resource "azurerm_virtual_network" "aegis_vnet" {
  name                = "vnet-aegis-ops"
  location            = azurerm_resource_group.aegis_rg.location
  resource_group_name = azurerm_resource_group.aegis_rg.name
  address_space       = ["10.0.0.0/16"]
}

# Subnet for AKS
resource "azurerm_subnet" "aks_subnet" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.aegis_rg.name
  virtual_network_name = azurerm_virtual_network.aegis_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Azure Kubernetes Service (AKS) Cluster
resource "azurerm_kubernetes_cluster" "aegis_aks" {
  name                = "aks-aegis-ops"
  location            = azurerm_resource_group.aegis_rg.location
  resource_group_name = azurerm_resource_group.aegis_rg.name
  dns_prefix          = "aegisops"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_DS2_v2"
    vnet_subnet_id = azurerm_subnet.aks_subnet.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
  }

  tags = {
    Environment = "Production"
    Project     = "Aegis-Ops"
    Architect   = "Mohamed Abdelrahman"
  }
}

output "kubernetes_cluster_name" {
  value = azurerm_kubernetes_cluster.aegis_aks.name
}

output "kube_config" {
  value     = azurerm_kubernetes_cluster.aegis_aks.kube_config_raw
  sensitive = true
}
