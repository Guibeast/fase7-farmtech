# FarmTech Solutions - Fase 1
# Analise estatistica R SOBRE A METEOROLOGIA (dados reais da API Open-Meteo).
#
# Uso:
#   Rscript analise_r/analise_clima.R
#
# Le data/clima_cidades.csv (snapshot das 18 cidades agricolas, gerado pelo
# dashboard a partir da API) e gera em analise_r/saidas/:
#   - estatisticas_clima.txt
#   - clima_et0_por_cidade.png
#   - clima_temp_vs_et0.png

dir_script <- tryCatch(
  dirname(sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))),
  error = function(e) "."
)
if (length(dir_script) == 0 || dir_script == "") dir_script <- "analise_r"

csv_path <- file.path(dir_script, "..", "data", "clima_cidades.csv")
saidas   <- file.path(dir_script, "saidas")
dir.create(saidas, showWarnings = FALSE, recursive = TRUE)

if (!file.exists(csv_path)) stop("CSV nao encontrado: ", csv_path)
dados <- read.csv(csv_path, encoding = "UTF-8")
vars <- c("Temperatura", "Umidade_Ar", "Temp_Solo",
          "Umidade_Solo_VWC", "ET0_Hoje", "Chuva_7d", "UV_Hoje", "Vento")

# ---- Estatistica descritiva ----
txt <- file.path(saidas, "estatisticas_clima.txt")
sink(txt)
cat("FarmTech - Analise Estatistica da Meteorologia (Fase 1)\n")
cat("Fonte: API Open-Meteo |", nrow(dados), "cidades agricolas\n\n")

cat("== Resumo descritivo ==\n")
print(summary(dados[vars]))

cat("\n== Media / Mediana / Desvio-padrao ==\n")
resumo <- data.frame(
  Media   = sapply(dados[vars], mean),
  Mediana = sapply(dados[vars], median),
  Desvio  = sapply(dados[vars], sd)
)
print(round(resumo, 2))

cat("\n== Correlacao (ET0 x demais variaveis) ==\n")
print(round(cor(dados[vars])["ET0_Hoje", ], 3))
sink()

# ---- Graficos ----
ord <- order(dados$ET0_Hoje)
png(file.path(saidas, "clima_et0_por_cidade.png"), width = 1000, height = 600)
par(mar = c(12, 4, 4, 2))
barplot(dados$ET0_Hoje[ord], names.arg = dados$Cidade[ord], las = 2,
        col = "darkseagreen", border = "white",
        main = "Evapotranspiracao (ET0) por cidade agricola",
        ylab = "ET0 hoje (mm)")
dev.off()

png(file.path(saidas, "clima_temp_vs_et0.png"), width = 800, height = 500)
plot(dados$Temperatura, dados$ET0_Hoje,
     main = "Temperatura vs Evapotranspiracao (ET0)",
     xlab = "Temperatura (C)", ylab = "ET0 hoje (mm)",
     pch = 19, col = rgb(0.2, 0.5, 0.2, 0.6))
abline(lm(ET0_Hoje ~ Temperatura, data = dados), col = "red", lwd = 2)
dev.off()

cat("Analise meteorologica concluida. Saidas em:", saidas, "\n")
