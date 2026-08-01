# Principios de Terraform/AWS para agentes

## Principios fundamentales

- Optimizar siempre para:

  1. capacidad de destruir (destroyability)
  2. entornos de desarrollo de bajo costo
  3. reproducibilidad
  4. propiedad explícita de los recursos
- Nunca asumir que los "valores por defecto empresariales" son apropiados
  para demos/MVPs.
- Todo recurso creado debe estar:

  - declarado
  - etiquetado (tagged)
  - ser destruible
  - ser trazable

---

## Reglas de entorno

### DEV / SANDBOX

- Usar:
  force_destroy = true
  para:

  - buckets S3
  - recursos de almacenamiento no productivos
- Desactivar el versionado de S3 a menos que sea explícitamente requerido.
- Usar políticas de retención mínimas:

  - CloudWatch Logs: 1–7 días
  - expiración por lifecycle de S3 cuando sea posible
- Evitar servicios gestionados costosos a menos que estén explícitamente
  aprobados:

  - NAT Gateway
  - MWAA
  - Redshift
  - OpenSearch
  - configuraciones de Bedrock a escala de producción
- Preferir arquitecturas serverless y amigables con el free tier.

---

## Reglas de logging

- NUNCA depender de log groups auto-creados por AWS.
- Declarar explícitamente todos los CloudWatch Log Groups en Terraform.
- Definir:

  - retention_in_days
  - tags
- Asegurar que los servicios dependan de log groups gestionados.

Ejemplos de objetivos:

- Lambda
- Step Functions
- Glue
- ECS
- API Gateway

---

## Reglas de S3

- Los buckets deben incluir:

  - tags
  - consideraciones de lifecycle
  - propiedad explícita
- Por defecto:

  - versionado desactivado en dev
  - encriptación activada solo si se requiere
- Evitar objetos ocultos fuera del ciclo de vida de Terraform.

---

## Reglas del ciclo de vida de Terraform

- Todo módulo debe soportar:
  terraform apply
  terraform destroy
  terraform apply

sin limpieza manual.

- Nunca crear recursos fuera de Terraform a menos que esté explícitamente
  documentado.
- Evitar recursos huérfanos.
- Preferir dependencias explícitas sobre comportamiento implícito.

---

## Reglas de control de costos

- Todo recurso debe incluir tags estándar:

  - Environment
  - Project
  - Owner
  - ManagedBy=Terraform
- Minimizar:

  - recursos siempre encendidos (always-on)
  - capacidad aprovisionada
  - infraestructura inactiva
- Preferir:

  - on-demand
  - serverless
  - entornos efímeros

---

## Reglas de diseño de módulos

- Los módulos deben exponer:

  - flags de activación (enable flags)
  - valores por defecto sensibles al entorno
  - configuración de retención
  - personalización de nombres
- Separar explícitamente el comportamiento de:

  - dev
  - staging
  - prod

---

## Reglas de seguridad para agentes

- NUNCA:

  - activar el versionado automáticamente
  - crear un NAT Gateway automáticamente
  - crear recursos costosos por defecto
  - aplicar retención de logs infinita
  - crear recursos no gestionados
- SIEMPRE preguntar antes de:

  - escalar privilegios IAM
  - persistencia de grado producción
  - recursos cross-account
  - servicios de AWS pagos fuera del free tier

---

## Reglas de validación

Antes de considerar la infraestructura completa, validar:

- terraform fmt
- terraform validate
- terraform plan
- terraform apply
- terraform destroy

Y verificar:

- que no haya log groups huérfanos
- que no haya buckets sin eliminar
- que no haya recursos de networking residuales
- que no haya recursos inesperados con riesgo de facturación

---

## Filosofía de arquitectura

- Demo != Producción
- Simplicidad > sobreingeniería empresarial
- La capacidad de destruir es parte de la arquitectura
- Infraestructura explícita > valores por defecto mágicos
- La ingeniería consciente del costo es obligatoria
