try:
    import argparse
except ImportError:
    print("Please check if module 'argparse' is installed")
    quit()

parser = argparse.ArgumentParser()
parser.add_argument('--matrix', type=argparse.FileType('r'), required=True,
                    help="Original matrix with results of primary metabolism summary")
parser.add_argument('--anno', type=argparse.FileType('r'), required=True,
                    help="eggNOG-mapper output file")
parser.add_argument('--out', type=str, required=True)
args = parser.parse_args()


def original_table_parsing(matrix, matrix_dict, species_list):
    header = matrix.readline()
    for line in matrix:
        description = line.strip().split("\t")
        ko, values = description[4], description[8:]
        matrix_dict[ko] = {species: 0 for species in species_list}
        for species in species_list:
            matrix_dict[ko][species] += int(values[species_list.index(species)])


def annotation_parsing(anno, anno_dict):
    for line in anno:
        if not line.startswith("#"):
            description = line.strip().split("\t")
            pep_ID, values = description[0], description[1:]
            if len(values[7]) != 0: # KEGG_ko
                for ko in values[7].split(","):
                    ko_ID = ko.split(":")[1]
                    if ko_ID not in anno_dict.keys():
                        anno_dict[ko_ID] = []
                        anno_dict[ko_ID].append(pep_ID)
                    elif ko_ID in anno_dict.keys():
                        anno_dict[ko_ID].append(pep_ID)


def output_creating(species_list, matrix_dict, anno_dict, out):
    Amo_pr_X4_dict = {}
    for ko in matrix_dict.keys():
        if ko in anno_dict.keys():
            Amo_pr_X4_dict[ko] = len(set(anno_dict[ko]))
        else:
            Amo_pr_X4_dict[ko] = 0

    with open("{out}.tab".format(out=out), 'a') as output:
        output.write("KOs\tAmo_pr_X4\t{species}\n".format(species="\t".join(species_list)))
        for ko, values in matrix_dict.items():
            species_values = []
            for species in species_list:
                species_values.append(str(values[species]))
            output.write("{group}\t{x4}\t{species}\n".format(group=ko, x4=Amo_pr_X4_dict[ko],
                                                             species="\t".join(species_values)))


if __name__ == "__main__":
    species_list = ["Aca_ca", "All_ma", "Amp_sp", "Ant_lo", "Bat_de", "Bla_br", "Cap_ow", "Cat_an", "Chr_pe",
                    "Cop_ci", "Cor_li", "Dic_pu", "Enc_cu", "Enc_in", "Ent_bi", "Ent_hi", "Fon_al", "Gan_pr",
                    "Ich_ho", "Lei_ma", "Mit_da", "Mon_br", "Mor_ve", "Nae_gr", "Nem_pa", "Nos_ce", "Par_at",
                    "Par_sa", "Par_tr", "Phy_in", "Pla_fa", "Pol_pa", "Roz_al", "Sal_ro", "Sch_po", "Sph_ar",
                    "Spi_pu", "The_tr", "Tox_go", "Try_br", "Ust_ma"]
    matrix_dict, annot_dict = {}, {}
    print("***** Input matrix parsing *****")
    original_table_parsing(args.matrix, matrix_dict, species_list)
    print("***** Input table parsing *****")
    annotation_parsing(args.anno, annot_dict)
    print("***** Output file creating *****")
    output_creating(species_list, matrix_dict, annot_dict, args.out)