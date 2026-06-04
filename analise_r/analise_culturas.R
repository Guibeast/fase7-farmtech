# FarmTech Solutions - Fase 1
# Analise estatistica dos dados agricolas (base R, sem pacotes externos).
#
# Uso:
#   Rscript analise_r/analise_culturas.R
#
# Gera em analise_r/saidas/:
#   - estatisticas.txt        resumo descritivo + correlacoes
#   - histograma_produtividade.png
#   - boxplots_variaveis.png
#   - dispersao_umidade_produtividade.png

dir_script <- tryCatch(
  dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))),
  error = function(e) "."
)
if (length(dir_script) == 0 || dir_script == "") dir_script <- "analise_r"

csv_path <- file.path(dir_script, "..", "data", "dados_agricolas.csv")
saidas   <- file.path(dir_script, "saidas")
dir.create(saidas, showWarnings = FALSE, recursive = TRUE)

if (!file.exists(csv_path)) stop("CSV nao encontrado: ", csv_path)
dados <- read.csv(csv_path)
vars <- c("Umidade_Solo", "pH_Solo", "Temperatura_Ambiente",
          "Nivel_N", "Historico_Irrigacao_mm", "Produtividade_Esperada")

# ---- Estatistica descritiva ----
txt <- file.path(saidas, "estatisticas.txt")
sink(txt)
cat("FarmTech - Analise Estatistica (Fase 1)\n")
cat("Amostras:", nrow(dados), "\n\n")

cat("== Resumo descritivo ==\n")
print(summary(dados[vars]))

cat("\n== Media / Mediana / Desvio-padrao ==\n")
resumo <- data.frame(
  Media   = sapply(dados[vars], mean),
  Mediana = sapply(dados[vars], median),
  Desvio  = sapply(dados[vars], sd),
  Minimo  = sapply(dados[vars], min),
  Maximo  = sapply(dados[vars], max)
)
print(round(resumo, 2))

cat("\n== Matriz de correlacao ==\n")
print(round(cor(dados[vars]), 3))
sink()

# ---- Graficos ----
png(file.path(saidas, "histograma_produtividade.png"), width = 800, height = 500)
hist(dados$Produtividade_Esperada,
     main = "Distribuicao da Produtividade Esperada",
     xlab = "Produtividade (kg/ha)", col = "darkseagreen", border = "white")
dev.off()

png(file.path(saidas, "boxplots_variaveis.png"), width = 900, height = 500)
par(mar = c(8, 4, 4, 2))
boxplot(scale(dados[vars]), las = 2, col = "lightsteelblue",
        main = "Boxplots das variaveis (padronizadas)")
dev.off()

png(file.path(saidas, "dispersao_umidade_produtividade.png"), width = 800, height = 500)
plot(dados$Umidade_Solo, dados$Produtividade_Esperada,
     main = "Umidade do Solo vs Produtividade",
     xlab = "Umidade do Solo (%)", ylab = "Produtividade (kg/ha)",
     pch = 19, col = rgb(0.2, 0.5, 0.2, 0.4))
abline(lm(Produtividade_Esperada ~ Umidade_Solo, data = dados), col = "red", lwd = 2)
dev.off()

cat("Analise concluida. Saidas em:", saidas, "\n")
