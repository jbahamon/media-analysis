#!/usr/bin/env Rscript

library(ggplot2)
library(reshape2)
args <- commandArgs(trailingOnly=TRUE)

if (length(args) < 3) {
    stop("Exactly three args are needed: modularities and conductance file, output folder and
         similarity name.\n", call.=FALSE)
} else {
    mod_cond <- args[1]
    folder <- args[2]
    name <- args[3]
}


mods_conds <- read.csv2(mod_cond, dec=".", sep="\t", check.names=FALSE)
mods_conds <- melt(mods_conds, id="n")
mods_conds$Metric <- mods_conds$variable

ggplot(mods_conds, aes(x=n, y=value, color=Metric)) +
    geom_line() +
    geom_point() + 
    labs(x="Number of communities", y="Value", 
         title=paste("Community discovery metrics for", name, "term set", sep=" ")) +
    theme(legend.position = c(1,1),legend.justification = c(1,1),
          panel.grid.minor.x = element_blank()) +
    scale_x_continuous(breaks = seq(1,19,1))  +
    scale_y_continuous(breaks = seq(0,1, 0.25), minor_breaks = seq(0,1, 0.125))

ggsave(paste(folder, "/", name, "_modularity_conductance.png", sep=""))

