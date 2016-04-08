#!/usr/bin/env Rscript

library(ggplot2)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 2) {
    stop("Exactly two args are needed: similarity file and output folder.\n", call.=FALSE)
} else {
    degrees <- args[1]
    folder <- args[2]
}


degrees <- read.csv2(degrees, header=FALSE, dec=".", sep=";", check.names=FALSE)

ggplot(degrees, aes(x=V1)) +
    geom_histogram(aes(y=..density..), color="black", fill="white",
                   binwidth=density(degrees$V1)$bw) +
    geom_line(stat="density",size=1) + 
    labs(x="Weighted Degree", y="Density", title="Weighted Degree Distribution") +
    theme(legend.position = c(1,1),legend.justification = c(1,1))

ggsave(paste(folder, "/Degree_distribution.png", sep=""))

