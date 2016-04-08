#!/usr/bin/env Rscript

library(ggplot2)
library(reshape)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 3) {
    stop("Exactly three args are needed: follower diversity file, output folder and name prefix.\n", call.=FALSE)
} else {
    diversity <- args[1]
    folder <- args[2]
    name <- args[3]
}


follower_diversity <- read.csv2(diversity, header=TRUE, sep=";", check.names=FALSE)
# I'm melting...
melted <- melt(follower_diversity, id.vars="Number of communities")
melted$value <- as.numeric(paste(melted$value))
melted$clusters <- as.factor(melted[["Number of communities"]])

ggplot(melted, aes(x=melted$clusters, y=melted$value, fill=melted$variable)) + 
    geom_bar(position="dodge", stat="identity") +
    labs(fill = "Only follows community outlets", 
         x="Number of communities followed", 
         y="Number of users",
         title="Media consumption diversity") + 
    theme(legend.position = c(1,1),legend.justification = c(1, 1)) +
    scale_fill_discrete(labels=c("Yes", "No")) 

ggsave(paste(folder,"/", name, "_follower_diversity.png", sep=""))
