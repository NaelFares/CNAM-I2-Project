# Benchmark IA CSV

- Date: `2026-05-04T23:02:57`
- CSV: `backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv`
- Ollama: `http://ia-services:11434`
- Acceleration demandee: `cpu`
- Repeats: `1`
- Modeles: `qwen2.5:1.5b-instruct, qwen2.5-coder:1.5b-instruct, llama3.2:1b`

## Synthese

| Modele | Reussite | Temps moyen | Temps min | Confiance moyenne |
| --- | ---: | ---: | ---: | ---: |
| qwen2.5:1.5b-instruct | 1/1 | 75.028s | 75.028s | 0.99 |
| qwen2.5-coder:1.5b-instruct | 1/1 | 276.557s | 276.557s | 1.0 |
| llama3.2:1b | 0/1 | n/a | n/a | n/a |

## Details par modele

### qwen2.5:1.5b-instruct

| Run | Statut | Temps | Evenements | Success ratio | Confiance | Detail |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | OK | 75.028s | 40 | 1.0 | 0.99 | Mapping des colonnes du JSON vers le format de planning |

### qwen2.5-coder:1.5b-instruct

| Run | Statut | Temps | Evenements | Success ratio | Confiance | Detail |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | OK | 276.557s | 40 | 1.0 | 1.0 | Mapping des champs nécessaires à partir de l'échantillon JSON. |

### llama3.2:1b

| Run | Statut | Temps | Evenements | Success ratio | Confiance | Detail |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 1 | KO | 143.796s | n/a | n/a | n/a | Aucun evenement valide reconstruit depuis le mapping IA |

## Modeles charges dans Ollama apres benchmark

| Modele | Taille | Processeur | Expiration |
| --- | ---: | --- | --- |
| llama3.2:1b | 1447469056 |  | 2026-05-04T23:12:57.395719583Z |
| qwen2.5-coder:1.5b-instruct | 1097538048 |  | 2026-05-04T23:12:11.10575052Z |
| qwen2.5:1.5b-instruct | 1097538048 |  | 2026-05-04T23:10:59.658243499Z |
