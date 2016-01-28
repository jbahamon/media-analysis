#!/usr/bin/env Rscript

library(ggplot2)
library(reshape)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 3) {
    stop("Exactly three args are needed: cluster sizes file, follower diversity file and output folder.\n", call.=FALSE)
} else {
    sizes <- args[1]
    diversity <- args[2]
    folder <- args[3]
}


cluster_sizes <- read.csv2(sizes, header=TRUE, sep=";", check.names=FALSE)
follower_diversity <- read.csv2(diversity, header=TRUE, sep=";", check.names=FALSE)

cluster_sizes$ID <- as.factor(cluster_sizes$ID)

# I'm melting...
melted <- melt(follower_diversity, id.vars="clusters")
melted$value <- as.numeric(paste(melted$value))
melted$clusters <- as.factor(melted$clusters)


ggplot(cluster_sizes, aes(x=cluster_sizes$ID, y=cluster_sizes$followers)) + 
    geom_bar(stat="identity") +
    labs(x="Cluster ID", y="Number of followers",
     title="Cluster audience size")
ggsave(paste(folder, "/Cluster_sizes.png", sep=""))


ggplot(melted, aes(x=melted$clusters, y=melted$value, fill=melted$variable)) + 
    geom_bar(position="dodge", stat="identity") +
    labs(fill = "Only follows clustered outlets", 
         x="Number of clusters followed", 
         y="Number of users",
         title="Media consumption diversity") + 
    theme(legend.position = c(1,1),legend.justification = c(1, 1)) +
    scale_fill_discrete(name = "Only follows clustered outlets",
                          breaks=c("exclusive", "with_zero"),
                          labels=c("Yes", "No"))


ggsave(paste(folder,"/Follower_diversity.png", sep=""))
