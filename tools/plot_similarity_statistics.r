#!/usr/bin/env Rscript

library(ggplot2)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 3) {
    stop("Exactly three args are needed: similarity file, output folder and
         similarity name.\n", call.=FALSE)
} else {
    similarity <- args[1]
    folder <- args[2]
    name <- args[3]
}

theme_set(theme_gray(base_size = 18))

similarities <- read.csv2(similarity, header=FALSE, dec=".", sep=";", check.names=FALSE)

ggplot(similarities, aes(x=V1)) +
    geom_histogram(aes(y=..density..), color="black", fill="white",
                   binwidth=density(similarities$V1)$bw) +
    geom_line(stat="density",size=1) + 
    labs(x="Similarity", y="Density", title=paste(name, 
                                                  "Similarity Distribution", sep=" ")) +
    theme(legend.position = c(1,1),legend.justification = c(1,1)) + 
    scale_x_continuous(breaks=seq(-1,1,0.1))

ggsave(paste(folder, "/", name, "_similarity_distribution.pdf", sep=""))

