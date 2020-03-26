try:
    import argparse
except ImportError:
    print("Please check if module 'argparse' is installed")
    quit()


parser = argparse.ArgumentParser()
parser.add_argument('--rbbh_pairs', type=argparse.FileType('r'), required=True)
parser.add_argument('--first_tag', type=str, required=True, help="For example: Psimillimum")
parser.add_argument('--second_tag', type=str, required=True, help="For example: Spseudoglobulus")
parser.add_argument('--first_gene_map', type=argparse.FileType('r'), required=True,
                    help="Table for first species with 3 columns: gene_ID, transcript_ID, protein_ID")
parser.add_argument('--second_gene_map', type=argparse.FileType('r'), required=True,
                    help="Table for second species with 3 columns: gene_ID, transcript_ID, protein_ID")
parser.add_argument('--red_first', type=argparse.FileType('r'), required=True,
                    help="File with first species gene IDs (one per line) which have redia-specific expression")
parser.add_argument('--cer_first', type=argparse.FileType('r'), required=True,
                    help="File with first species gene IDs (one per line) which have cercaria-specific expression")
parser.add_argument('--mar_first', type=argparse.FileType('r'), required=True,
                    help="File with first species gene IDs (one per line) which have marita-specific expression")
parser.add_argument('--red_second', type=argparse.FileType('r'), required=True,
                    help="File with second species gene IDs (one per line) which have redia-specific expression")
parser.add_argument('--cer_second', type=argparse.FileType('r'), required=True,
                    help="File with second species gene IDs (one per line) which have cercaria-specific expression")
parser.add_argument('--mar_second', type=argparse.FileType('r'), required=True,
                    help="File with second species gene IDs (one per line) which have marita-specific expression")
parser.add_argument('--output', type=str, required=True)
args = parser.parse_args()


def gene_map_parsing(gene_dict, gene_map):
    header = gene_map.readline()
    for line in gene_map:
        description = line.strip().split("\t")
        gene_ID, transcript_ID, protein_ID = description[0].strip(), description[1].strip(), description[2].strip()
        gene_dict[gene_ID] = {"transcript": transcript_ID, "protein": protein_ID}


def RBBH_pairs_parsing(rbbh_pairs, pair_prot_dict):
    header = rbbh_pairs.readline()
    for line in rbbh_pairs:
        description = line.strip().split("\t")
        pair_ID, first_sp, second_sp = description[0], description[1], description[2]
        pair_prot_dict[pair_ID] = {"first_sp": first_sp, "second_sp": second_sp,
                               "first_specificity": [], "second_specificity": []}


def add_specificity(pair_prot_dict, gene_map, stage_specific_genes, species_tag, stage_tag):
    for line in stage_specific_genes:
        gene = line.strip().split("\t")[0]
        if gene in gene_map.keys():
            for pair, values in pair_prot_dict.items():
                if gene_map[gene]["protein"] == values["{tag}_sp".format(tag=species_tag)]:
                    values["{tag}_specificity".format(tag=species_tag)].append(stage_tag)


def RBBH_prot_2_genes(pair_prot_dict, pair_genes_dict, sp1_gene_dict, sp2_gene_dict):
    for pair, values in pair_prot_dict.items():
        gene_pair = []
        for sp1_gene, sp1_map_values in sp1_gene_dict.items():
            if sp1_map_values["protein"] == values["first_sp"]:
                gene_pair.append(sp1_gene)
                break

        for sp2_gene, sp2_map_values in sp2_gene_dict.items():
            if sp2_map_values["protein"] == values["second_sp"]:
                gene_pair.append(sp2_gene)
                break
        if len(gene_pair) == 2:
            pair_genes_dict[pair] = {"first_sp": gene_pair[0], "second_sp": gene_pair[1],
                                      "first_specificity": values["first_specificity"],
                                      "second_specificity": values["second_specificity"]}


def jaccard_similarity(one_list, other_list):
    """
    FROM: http://dataconomy.com/2015/04/implementing-the-five-most-popular-similarity-measures-in-python/
    The function measure the similarity between two sets of genes (Jaccard similarity index)
    @param one_list: list of genes
    @param other_list: list of genes
    """
    intersection_cardinality = len(set.intersection(*[set(one_list), set(other_list)]))
    union_cardinality = len(set.union(*[set(one_list), set(other_list)]))
    if union_cardinality != 0:
        return round(intersection_cardinality / float(union_cardinality), 2)
    else:
        return 0


def specificity_comparison(pair_gene_dict, first_stage_tag, second_stage_tag, Jaccard_dict, Intersection_dict):
    first = [pair for pair in pair_gene_dict.keys() if pair_gene_dict[pair]["first_specificity"][0] == first_stage_tag]
    second = [pair for pair in pair_gene_dict.keys() if pair_gene_dict[pair]["second_specificity"][0] == second_stage_tag]
    Jaccard_dict["first_{first_stage_tag}_vs_second_{second_stage_tag}".format(
        first_stage_tag=first_stage_tag, second_stage_tag=second_stage_tag)] = jaccard_similarity(first, second)
    Intersection_dict["first_{first_stage_tag}_vs_second_{second_stage_tag}".format(
        first_stage_tag=first_stage_tag, second_stage_tag=second_stage_tag)] = len(set.intersection(*[set(first),
                                                                                                      set(second)]))


def output_files_creating(Intersection_dict, Jaccard_dict, pair_gene_dict, first_tag, second_tag, output):
    with open("{output}.Jaccard_RBBH_pairs_specificity.tsv".format(output=output), 'a') as Jaccard_output:
        Jaccard_output.write("{first_tag}\{second_tag}\tRediae\tCercariae\tMarita\n".format(first_tag=first_tag,
                                                                                            second_tag=second_tag))
        Jaccard_output.write("Rediae\t{red_vs_red}\t{red_vs_cer}\t{red_vs_mar}\n".format(
                                red_vs_red=Jaccard_dict["first_R_vs_second_R"],
                                red_vs_cer=Jaccard_dict["first_R_vs_second_C"],
                                red_vs_mar=Jaccard_dict["first_R_vs_second_M"]))
        Jaccard_output.write("Cercariae\t{cer_vs_red}\t{cer_vs_cer}\t{cer_vs_mar}\n".format(
                                cer_vs_red=Jaccard_dict["first_C_vs_second_R"],
                                cer_vs_cer=Jaccard_dict["first_C_vs_second_C"],
                                cer_vs_mar=Jaccard_dict["first_C_vs_second_M"]))
        Jaccard_output.write("Marita\t{mar_vs_red}\t{mar_vs_cer}\t{mar_vs_mar}\n".format(
                                mar_vs_red=Jaccard_dict["first_M_vs_second_R"],
                                mar_vs_cer=Jaccard_dict["first_M_vs_second_C"],
                                mar_vs_mar=Jaccard_dict["first_M_vs_second_M"]))

    with open("{output}.RBBH_pairs_and_specificity.tsv".format(output=output), 'a') as RBBH_output:
        RBBH_output.write("RBBH_pair_ID\t{first}_seq_ID\t{second}_seq_ID\t{first}_specificity\t{second}_specificity\n".format(
            first=first_tag, second=second_tag))
        for pair, values in pair_gene_dict.items():
            RBBH_output.write("{pair}\t{first}\t{second}\t{first_specificity}\t{second_specificity}\n".format(
                pair=pair, first=values["first_sp"], second=values["second_sp"],
                first_specificity=values["first_specificity"][0], second_specificity=values["second_specificity"][0]
            ))

    with open("{output}.RBBH_pairs_specificity_intersection.tsv".format(output=output), 'a') as Intersection_output:
        Intersection_output.write("{first_tag}_vs_{second_tag}_samples\tNumber_of_RBBH_pairs_with_common_specificity\n".format(
            first_tag=first_tag, second_tag=second_tag))
        Intersection_output.write("{first_tag}_rediae_vs_{second_tag}_rediae\t{red_vs_red}\n".format(
            first_tag=first_tag, second_tag=second_tag, red_vs_red=Intersection_dict["first_R_vs_second_R"]))
        Intersection_output.write("{first_tag}_rediae_vs_{second_tag}_cercariae\t{red_vs_cer}\n".format(
            first_tag=first_tag, second_tag=second_tag, red_vs_cer=Intersection_dict["first_R_vs_second_C"]))
        Intersection_output.write("{first_tag}_rediae_vs_{second_tag}_marita\t{red_vs_mar}\n".format(
            first_tag=first_tag, second_tag=second_tag, red_vs_mar=Intersection_dict["first_R_vs_second_M"]))
        Intersection_output.write("{first_tag}_cercariae_vs_{second_tag}_rediae\t{cer_vs_red}\n".format(
            first_tag=first_tag, second_tag=second_tag, cer_vs_red=Intersection_dict["first_C_vs_second_R"]))
        Intersection_output.write("{first_tag}_cercariae_vs_{second_tag}_cercariae\t{cer_vs_cer}\n".format(
            first_tag=first_tag, second_tag=second_tag, cer_vs_cer=Intersection_dict["first_C_vs_second_C"]))
        Intersection_output.write("{first_tag}_cercariae_vs_{second_tag}_marita\t{cer_vs_mar}\n".format(
            first_tag=first_tag, second_tag=second_tag, cer_vs_mar=Intersection_dict["first_C_vs_second_M"]))
        Intersection_output.write("{first_tag}_marita_vs_{second_tag}_rediae\t{mar_vs_red}\n".format(
            first_tag=first_tag, second_tag=second_tag, mar_vs_red=Intersection_dict["first_M_vs_second_R"]))
        Intersection_output.write("{first_tag}_marita_vs_{second_tag}_cercariae\t{mar_vs_cer}\n".format(
            first_tag=first_tag, second_tag=second_tag, mar_vs_cer=Intersection_dict["first_M_vs_second_C"]))
        Intersection_output.write("{first_tag}_marita_vs_{second_tag}_marita\t{mar_vs_mar}\n".format(
            first_tag=first_tag, second_tag=second_tag, mar_vs_mar=Intersection_dict["first_M_vs_second_M"]))


if __name__ == "__main__":
    sp1_gene_map_dict, sp2_gene_map_dict, pair_prot_dict, pair_gene_dict, Jaccard_dict, Intersection_dict = \
        {}, {}, {}, {}, {}, {}
    gene_map_parsing(sp1_gene_map_dict, args.first_gene_map)
    gene_map_parsing(sp2_gene_map_dict, args.second_gene_map)
    RBBH_pairs_parsing(args.rbbh_pairs, pair_prot_dict)
    add_specificity(pair_prot_dict, sp1_gene_map_dict, args.red_first, "first", "R")
    add_specificity(pair_prot_dict, sp1_gene_map_dict, args.cer_first, "first", "C")
    add_specificity(pair_prot_dict, sp1_gene_map_dict, args.mar_first, "first", "M")
    add_specificity(pair_prot_dict, sp2_gene_map_dict, args.red_second, "second", "R")
    add_specificity(pair_prot_dict, sp2_gene_map_dict, args.cer_second, "second", "C")
    add_specificity(pair_prot_dict, sp2_gene_map_dict, args.mar_second, "second", "M")
    for pair, values in pair_prot_dict.items():
        if len(values["first_specificity"]) == 0:
            values["first_specificity"].append("-")

        if len(values["second_specificity"]) == 0:
            values["second_specificity"].append("-")
    RBBH_prot_2_genes(pair_prot_dict, pair_gene_dict, sp1_gene_map_dict, sp2_gene_map_dict)
    specificity_comparison(pair_gene_dict, "R", "R", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "R", "C", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "R", "M", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "C", "R", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "C", "C", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "C", "M", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "M", "R", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "M", "C", Jaccard_dict, Intersection_dict)
    specificity_comparison(pair_gene_dict, "M", "M", Jaccard_dict, Intersection_dict)
    output_files_creating(Intersection_dict, Jaccard_dict, pair_gene_dict, args.first_tag, args.second_tag, args.output)