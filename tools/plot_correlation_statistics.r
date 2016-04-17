#!/usr/bin/env Rscript

library(ggplot2)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 3) {
    stop("Exactly three args are needed: similarity file, output folder and
         similarity name.\n", call.=FALSE)
} else {
    correlation <- args[1]
    folder <- args[2]
    name <- args[3]
}

theme_set(theme_gray(base_size = 18))

correlations <- read.csv2(correlation, header=FALSE, dec=".", sep="\t", check.names=FALSE)

ggplot(correlations, aes(x=V1,y=V2)) +
    geom_bin2d() +
    scale_fill_gradient(low="#EEEEEE", high="black", limits=c(1,NA), trans="log",
                        breaks=c(1,2,4,8,16,32,64,128)) +
    scale_x_continuous(breaks=seq(-1,1, 0.2), limits=c(-1,1)) + 
    theme(panel.background  = element_rect(fill="white"),
          panel.grid.major = element_line(color="#ebebeb"),
          panel.grid.minor = element_line(color="#ebebeb")) +
    labs(x="Correlation", y="Kurtosis", fill="Count", title="Correlation and Kurtosis Distribution for 'President' term set") + 
    theme(plot.title = element_text(size=18))



ggsave(paste(folder, "/", name, "_correlation_distribution.pdf", sep=""))

