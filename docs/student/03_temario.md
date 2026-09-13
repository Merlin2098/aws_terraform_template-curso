# Curso AWS Data Engineering — Temario (9 Sesiones)

> Reestructuración basada en
> [`data/guia_reestructuracion_curso_aws_data_engineer.md`](../../data/guia_reestructuracion_curso_aws_data_engineer.md).
> Objetivo de la reestructuración: dar una sesión completa a Data Streaming,
> integrar los tipos de almacenamiento en una narrativa arquitectónica y
> añadir el recorrido Data Lakehouse → Data Warehouse (Redshift), sin
> aumentar el número total de sesiones.

## Sesión 1 — Fundamentos de AWS y Preparación del Entorno

**Teoría**

* Fundamentos de Cloud Computing
* ¿Qué es AWS? Regiones y Availability Zones
* Modelo de responsabilidad compartida
* IAM: usuarios, roles, policies y principio de mínimo privilegio
* AWS CLI
* Git y GitHub — estructura inicial del repositorio
* Introducción a Claude Code — desarrollo asistido por IA
* Budgets, Cost Explorer y Pricing Calculator — control de costos desde el día 1

**Laboratorio**

* Configuración de la cuenta AWS
* Configuración de AWS CLI
* Creación de un usuario IAM
* Validación del acceso desde la terminal
* Configuración de un Budget con alerta de costos

**Objetivo:** dejar listo un entorno AWS funcional, seguro y con control de costos activado desde el inicio.

---

## Sesión 2 — Infrastructure as Code con Terraform

**Teoría**

* ¿Qué es Infrastructure as Code?
* Terraform Workflow: Providers, Resources, Variables, Outputs, Locals, Data Sources
* Organización del proyecto
* Terraform State
* Remote Backend (S3)
* `init` → `plan` → `apply` → `destroy`
* Uso responsable de Claude Code para asistir el desarrollo de infraestructura

**Laboratorio**

* Crear un bucket S3 mediante Terraform
* Modularizar ese recurso
* Ejecutar `plan` y `apply`

**Objetivo:** pasar de la configuración manual a una infraestructura declarativa, versionada y reproducible — es la base sobre la que se provisiona el resto del curso.

---

## Sesión 3 — Arquitecturas de Almacenamiento en AWS

Reemplaza la separación estricta entre "S3" y "bases de datos" por una
visión arquitectónica: dónde deben vivir los datos y por qué.

**Teoría**

* Amazon S3: object storage, buckets, capas `raw`/`processed`/`curated`, versionado, lifecycle policies
* Amazon RDS: modelo relacional, tablas/relaciones/índices, CRUD, cuándo elegir una base relacional
* Amazon DynamoDB: modelo NoSQL, Partition Key, Sort Key, access patterns, cuándo elegir DynamoDB
* Lambda como capa de integración: leer/escribir en S3, RDS y DynamoDB

> Alcance SQL/NoSQL: operaciones CRUD básicas en RDS y DynamoDB. Modelado
> avanzado, índices secundarios y access patterns complejos quedan fuera de
> esta sesión.

**Laboratorio**

* Crear un Data Lake sencillo en S3 (versionado y lifecycle)
* Crear una tabla DynamoDB, insertar y consultar registros
* Exploración guiada de Amazon RDS (demo del instructor)

**Objetivo:** distinguir entre almacenamiento analítico (S3/Data Lake), operacional relacional (RDS) y operacional NoSQL (DynamoDB), y saber cuándo usar cada uno.

---

## Sesión 4 — Serverless y Contenedores

**Teoría**

* ¿Qué es Serverless? AWS Lambda, execution roles, triggers e integraciones
* ¿Cuándo usar imágenes en vez de ZIP?
* Docker, Dockerfile, construcción de imágenes
* Amazon ECR
* Lambda mediante Container Images
* Conexión con el resto del curso: Lambda como componente que interactúa con S3, RDS, DynamoDB, EventBridge y streaming (Sesión 7)

**Laboratorio**

* Crear una Lambda sencilla
* Publicarla mediante una imagen en Amazon ECR

**Objetivo:** ejecutar lógica de procesamiento sin administrar servidores y conocer las dos formas de desplegar una Lambda (ZIP vs. imagen).

> Nota de ejecución: API Gateway queda como servicio complementario. El foco de la sesión es Lambda y cuándo es necesario usar Docker + ECR.

---

## Sesión 5 — Procesamiento Analítico con AWS Glue y Athena

**Teoría**

* Batch Processing y ETL
* AWS Glue: Crawlers, Data Catalog, Jobs, Triggers
* Amazon Athena: consultas SQL sobre datos en S3
* Introducción al concepto de Data Lakehouse (se profundiza en la Sesión 6)

**Laboratorio**

* Crear un Crawler
* Ejecutar un Job sencillo (bronze → silver/gold)
* Consultar información desde Athena

**Objetivo:** transformar datos almacenados en información consultable — de archivos crudos a datos confiables y consultables.

---

## Sesión 6 — Data Lakehouse, Data Warehouse y Analytics

Sesión más arquitectónica y analítica que orientada a servicios: la
evolución desde un Data Lake hacia Lakehouse, y cuándo aparece la necesidad
de un Data Warehouse.

**Teoría**

* Data Lake vs. Data Lakehouse vs. Data Warehouse — diferencias conceptuales
* Data Lakehouse: organización y gobierno sobre S3 + Glue Data Catalog + Athena (conceptual, sobre la infraestructura ya construida en la Sesión 5 — no se crea una tabla Lakehouse formal tipo Iceberg/Hudi)
* OLTP vs. OLAP
* ¿Cuándo aparece un Data Warehouse? Modelos dimensionales, BI y reporting
* Amazon Redshift: su rol como Data Warehouse administrado, cuándo usarlo frente a Athena, cómo recibe datos procesados desde S3
* Introducción a AWS Lake Formation — gobierno de datos sobre el Data Lake

**Laboratorio**

* Demo guiada del instructor: Amazon Redshift Serverless recibiendo datos procesados desde S3 (sin laboratorio individual del alumno, para evitar costo/complejidad operativa)

**Objetivo:** que el alumno pueda responder cuándo usaría S3, Athena, un Lakehouse o Redshift dentro de una arquitectura de datos.

---

## Sesión 7 — Data Streaming en AWS

Sesión completa dedicada a streaming — no queda como subtema de
orquestación.

**Teoría**

* Batch vs. Streaming
* Modelo productor-consumidor: evento, mensaje, producer, consumer, topic, partition, offset, consumer group
* Amazon MSK (Managed Streaming for Apache Kafka): qué administra AWS, qué sigue siendo responsabilidad del equipo, casos de uso
* Amazon Kinesis Data Streams: servicio nativo de streaming de AWS
* Comparación conceptual: Apache Kafka / Amazon MSK / Kinesis Data Streams
* Integración con AWS: producer → MSK/Kinesis → consumer (Lambda) → S3 / DynamoDB

**Laboratorio**

* Laboratorio 1 — Amazon MSK: crear un topic, producir y consumir eventos, persistir en S3/DynamoDB
* Laboratorio 2 — Amazon Kinesis Data Streams: crear un stream, producir y consumir eventos como alternativa nativa a MSK

**Objetivo:** comprender qué cambia en la arquitectura cuando ya no se puede esperar a que llegue un archivo completo, y construir una arquitectura de datos orientada a eventos.

> Nivel esperado: no se asume experiencia previa en streaming/mensajería. Los conceptos se explican desde cero antes de tocar la consola. No se profundiza en administración avanzada de clusters.

---

## Sesión 8 — Orquestación e Inteligencia Artificial Aplicada

Se mantienen juntas en una sesión, divididas en dos bloques integrados,
para conservar el total de 9 sesiones del curso.

**Bloque A — Orquestación**

* AWS Step Functions y sus estados
* Amazon EventBridge — triggers basados en eventos
* Manejo de errores, reintentos, dependencias
* Diferencia entre event-driven y workflow orchestration

**Bloque B — IA aplicada a datos**

* Introducción a Amazon Bedrock, Foundation Models
* Prompt Engineering
* Integración con Lambda
* Claude Code para desarrollo sobre AWS
* Límites y validación de resultados

**Laboratorio**

* Orquestar el pipeline de las Sesiones 5-6 con Step Functions
* Configurar un trigger con EventBridge
* Consumir un modelo de Bedrock desde una Lambda, usando como input datos reales generados por el pipeline

**Objetivo:** que el pipeline analítico deje de ser manual y se ejecute de forma orquestada, y comprender cómo integrar IA generativa sobre un pipeline de datos ya construido.

---

## Sesión 9 — Proyecto Final

Esta sesión se divide en dos componentes complementarios:

### A. Proyecto de referencia (desarrollado por el docente)

* El docente presenta un proyecto end-to-end ya construido que integra los servicios vistos en el curso (Terraform → Almacenamiento → Glue/Athena → Lakehouse/Redshift → Step Functions → Bedrock).
* Sirve como demo guiada: se recorre la arquitectura, se explican las decisiones de diseño, y se muestra el repositorio final como referencia de buenas prácticas.

### B. Proyecto final de los alumnos

* Los alumnos construyen su propio pipeline de datos aplicando el stack del curso, con libertad de elegir dataset/caso de uso.
* **Checklist mínimo de entrega:**
  * Infraestructura provisionada con Terraform
  * Data Lake organizado en S3 (con versionado/lifecycle)
  * Al menos un job de procesamiento (Glue) y consulta (Athena)
  * Pipeline orquestado (Step Functions o EventBridge)
  * Un caso de uso de IA generativa con Bedrock sobre los datos del pipeline
  * Repositorio en GitHub con README y documentación
* **Componente opcional (no obligatorio):** incorporar una rama de streaming (MSK o Kinesis) hacia S3/DynamoDB, para quien quiera profundizar más allá del mínimo.

**Teoría**

* Revisión de arquitectura y buenas prácticas de Terraform y AWS
* Documentación del proyecto y publicación en GitHub
* Certificación recomendada: **AWS Certified Data Engineer – Associate**
* Próximos pasos

**Objetivo:** que cada alumno cierre el curso con un repositorio propio, presentable, que integra el stack completo — usando el proyecto del docente como referencia de calidad.

---

## Resumen de cambios vs. la estructura anterior

| Cambio | Sesión afectada |
|---|---|
| Sesión de almacenamiento pasa de "solo S3" a arquitectura completa (S3 + RDS + DynamoDB + Lambda) | Sesión 3 |
| Athena se separa de Glue-procesamiento puro y gana su propia sesión de Lakehouse/Warehouse/Redshift | Sesión 5 (antes) → Sesión 6 (nueva) |
| Nueva sesión dedicada íntegramente a Streaming, con laboratorio de MSK y de Kinesis | Sesión 7 (antes compartida con Orquestación) |
| Redshift Serverless entra como demo del instructor, sin laboratorio individual | Sesión 6 (nueva) |
| Lake Formation se mueve de la sesión de procesamiento a la de Lakehouse/Warehouse | Sesión 6 (nueva) |
| Orquestación e IA se mantienen juntas para no aumentar el total de sesiones | Sesión 8 |
| Streaming es componente opcional del proyecto final, no obligatorio | Sesión 9 |
| Certificación específica en vez de mención genérica | Sesión 9 |

> Ver `data/guia_reestructuracion_curso_aws_data_engineer.md` sección 8 para
> el detalle de las decisiones de alcance resueltas (Kafka vs. MSK, Kinesis,
> profundidad de Redshift/Lakehouse, streaming en el proyecto final, nivel
> técnico esperado).
