# Curso AWS Data Engineering — Temario (9 Sesiones)

## Sesión 1 — Fundamentos de AWS y Preparación del Entorno

**Teoría**

* Introducción a Cloud Computing
* ¿Qué es AWS?
* Regiones y Availability Zones
* Modelo de responsabilidad compartida
* IAM: usuarios, grupos y roles
* Principio de mínimo privilegio
* AWS CLI
* Configuración del entorno de desarrollo
* Git y estructura del repositorio del curso
* Introducción a Claude Code — desarrollo asistido por IA
* **Nuevo:** Calculadora de Precios, Cost Explorer y Budgets — control de costos desde el día 1

**Laboratorio**

* Configuración de la cuenta AWS
* Configuración de AWS CLI
* Creación de un usuario IAM
* Validación del acceso desde la terminal
* **Nuevo:** Configuración de un Budget con alerta de costos

**Objetivo:** que todos lleguen con un entorno completamente funcional y con control de costos activado desde el inicio.

\---

## Sesión 2 — Infrastructure as Code con Terraform

**Teoría**

* ¿Qué es Infrastructure as Code?
* Terraform Workflow
* Providers, Resources, Variables, Outputs, Locals, Data Sources
* Modules
* Terraform State
* Remote Backend (S3)
* Organización del proyecto
* Uso de pre-commit para generar contexto del agente

**Laboratorio**

* Crear un bucket S3 mediante Terraform
* Modularizar ese recurso
* Ejecutar plan y apply

**Objetivo:** comprender el flujo básico de Terraform, ya que se usará como base para provisionar el resto del curso.

\---

## Sesión 3 — Data Lakes con Amazon S3

**Teoría**

* Fundamentos de Data Lake
* Amazon S3: buckets, objetos, organización de datasets
* Versionado
* Lifecycle Policies
* Bucket Policies
* Buenas prácticas

**Laboratorio**

* Crear un Data Lake sencillo
* Cargar archivos
* Configurar versionado y Lifecycle

**Objetivo:** comprender cómo organizar almacenamiento analítico.

\---

## Sesión 4 — Serverless y Contenedores

**Teoría**

* ¿Qué es Serverless?
* AWS Lambda, API Gateway, IAM Roles, ZIP Deployments
* ¿Cuándo usar imágenes?
* Introducción a Docker, Dockerfile, construcción de imágenes
* Amazon ECR
* Lambda mediante Container Images

**Laboratorio**

* Crear una Lambda sencilla
* Publicarla mediante una imagen en Amazon ECR

**Objetivo:** conocer las dos formas de desplegar una Lambda.

> Nota de ejecución: API Gateway queda como un servicio complementario. El foco de la sesión es comprender Lambda y cuándo es necesario utilizar Docker + ECR.---

## Sesión 5 — Bases de Datos

**Teoría**



SQL vs NoSQL

¿Cuándo utilizar una base de datos relacional?

¿Cuándo utilizar DynamoDB?

Amazon RDS (visión general)

Amazon DynamoDB

Modelado básico de tablas



**Laboratorio**

* Crear una tabla DynamoDB
* Insertar y consultar registros
* Exploración guiada de Amazon RDS (demo del instructor)

**Objetivo:** conocer ambos motores y cuándo utilizarlos.

\---

## Sesión 6 — Procesamiento de Datos

**Teoría**

* AWS Glue: Crawlers, Data Catalog, ETL Jobs, Triggers
* Amazon Athena
* **Nuevo:** Introducción a AWS Lake Formation — gobierno de datos sobre el Data Lake
* **Nuevo:** Athena vs. Redshift — cuándo usar cada uno (comparación conceptual, sin laboratorio)
* Flujo general de un pipeline analítico

**Laboratorio**

* Crear un Crawler
* Ejecutar un Job sencillo
* Consultar información desde Athena

**Objetivo:** recorrer el ciclo básico de procesamiento de datos y entender dónde encaja cada servicio analítico de AWS.

\---

## Sesión 7 — Orquestación y Streaming

**Teoría**

* ¿Por qué orquestar un pipeline?
* AWS Step Functions y sus estados
* Amazon EventBridge — triggers basados en eventos
* **Nuevo:** Introducción conceptual a streaming — Amazon Kinesis (qué es, cuándo usarlo vs. batch, sin laboratorio dedicado)

**Laboratorio**

* Orquestar el pipeline de la Sesión 6 con Step Functions
* Configurar un trigger con EventBridge

**Objetivo:** que el pipeline analítico deje de ser manual y se ejecute de forma automatizada y orquestada.

\---

## Sesión 8 — IA Generativa aplicada a AWS

**Teoría**

* Introducción a Amazon Bedrock
* Foundation Models
* Prompt Engineering
* Integración con Lambda
* Claude Code para desarrollo sobre AWS
* Casos de uso reales

**Laboratorio**

* Consumir un modelo de Bedrock desde una Lambda
* **Ajuste:** usar como input datos reales generados por el pipeline de las Sesiones 6-7 (conecta IA con el resto del curso en vez de quedar aislada)

**Objetivo:** comprender cómo integrar IA generativa sobre un pipeline de datos ya construido.

\---

## Sesión 9 — Proyecto Final

Esta sesión se divide en dos componentes complementarios:

### A. Proyecto de referencia (desarrollado por el docente)

* El docente presenta un proyecto end-to-end ya construido que integra todos los servicios vistos en el curso (Terraform → S3 → Glue/Athena → Step Functions → Bedrock).
* Sirve como **demo guiada**: se recorre la arquitectura, se explican las decisiones de diseño, y se muestra el repositorio final como referencia de "buenas prácticas".
* Función pedagógica: dar a los alumnos un ejemplo concreto de nivel esperado antes de que empiecen el suyo.

### B. Proyecto final de los alumnos (a desarrollar)

* Los alumnos construyen su propio pipeline de datos aplicando el stack completo del curso, con libertad de elegir dataset/caso de uso.
* **Checklist mínimo de entrega:**

  * Infraestructura provisionada con Terraform
  * Data Lake organizado en S3 (con versionado/lifecycle)
  * Al menos un job de procesamiento (Glue) y consulta (Athena)
  * Pipeline orquestado (Step Functions o EventBridge)
  * Un caso de uso de IA generativa con Bedrock sobre los datos del pipeline
  * Repositorio en GitHub con README y documentación

**Teoría**

* Revisión de arquitectura
* Buenas prácticas de Terraform y AWS
* Documentación del proyecto y publicación en GitHub
* **Ajuste:** certificación recomendada específica — **AWS Certified Data Engineer – Associate** (en vez de mención genérica a "certificaciones AWS")
* Próximos pasos

**Objetivo:** que cada alumno cierre el curso con un repositorio propio, presentable, que integra todo el stack — usando el proyecto del docente como referencia de calidad.

\---

## Resumen de cambios vs. la propuesta original

|Cambio|Sesión afectada|
|-|-|
|Se agregó control de costos (Budget/Cost Explorer)|Sesión 1|
|Se agregó Lake Formation + comparación Athena vs. Redshift|Sesión 6|
|Nueva sesión dedicada a Orquestación + intro a Kinesis|Sesión 7 (nueva)|
|Bedrock se movió al final y ahora usa datos reales del pipeline|Sesión 8 (antes Sesión 7)|
|Certificación específica en vez de mención genérica|Sesión 9|
|Proyecto final dividido en demo del docente + proyecto propio del alumno|Sesión 9|



