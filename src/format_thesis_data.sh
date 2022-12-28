# Declare Functions
remove_accents() {
	sed -e "s/ñ/n/g" \
		-e "s/á/a/g" \
		-e "s/ã/a/g" \
		-e "s/Á/A/g" \
		-e "s/à/a/g" \
		-e "s/À/A/g" \
		-e "s/ä/a/g" \
		-e "s/Ä/a/g" \
		-e "s/Ã/a/g" \
		-e "s/ç/c/g" \
		-e "s/é/e/g" \
		-e "s/É/E/g" \
		-e "s/è/e/g" \
		-e "s/ë/e/g" \
		-e "s/í/i/g" \
		-e "s/Í/I/g" \
		-e "s/ì/i/g" \
		-e "s/î/i/g" \
		-e "s/ï/i/g" \
		-e "s/ñ/n/g" \
		-e "s/Ñ/N/g" \
		-e "s/ó/o/g" \
		-e "s/Ó/O/g" \
		-e "s/ò/o/g" \
		-e "s/Ò/O/g" \
		-e "s/Ò/O/g" \
		-e "s/ö/o/g" \
		-e "s/õ/o/g" \
		-e "s/ú/u/g" \
		-e "s/Ú/U/g" \
		-e "s/ù/u/g" \
		-e "s/ô/o/g" \
		-e "s/û/u/g" \
		-e "s/Ü/U/g" \
		-e "s/ü/u/g" $1
}


# combine csv files
# https://unix.stackexchange.com/questions/293775/merging-contents-of-multiple-csv-files-into-single-csv-file
head -n 1 2022.csv > combined.out && tail -n+2 -q *.csv >> combined.out

# TODO: replace every "?" in author column with n (it's supposed to be ñ)
# output autor_asesor.csv and titles.csv
python formatter.py


#https://stackoverflow.com/questions/36689275/bash-split-line-into-multiple-lines
# https://stackoverflow.com/questions/5074893/how-to-remove-the-last-character-from-a-bash-grep-output
# remove 'sustentantes' from asesor column
cat autor_asesor.csv | tr -d '"' | while IFS="~" read -r -a line; do printf "%s\n" "${line[@]}"; done | grep asesor | rev | cut -c 10- | rev > asesores.txt

# remove accents
remove_accents combined.out > combined_sin_ac.out
remove_accents asesores.txt > asesores_sin_caract.txt

# sorted list of advisors by number of thesis in tab delimited format
sed 's/,*$//g' asesores_sin_caract.txt | sort | uniq -c | sort -n -r | sed $'s/^ *\([0-9]*\) */\\1\t/' > asesores_comunes.txt

# Loop to extract and print |n_thesis|supervisor name|first and las thesis year|Awarding Institution/Program|
while read p; do
  ASES=$(awk -F'\t' '{print $2}' <<< "$p")
#  NTES=$(awk -F'\t' '{print $1}' <<< "$p")
  COMB=$(grep '["~]'"$ASES.\{0,2\}asesor" combined_sin_ac.out)
  NTES=$(echo "$COMB" | wc -l)
  MAXMIN=$(awk -vFPAT='([^,]*)|("[^"]+")' -vOFS=, '{print $3}' <<< "$COMB"| ./maxmin.sh)
  INST=$(awk -vFPAT='([^,]*)|("[^"]+")' -vOFS=, '{print $5}' <<< "$COMB"| sort | uniq -c | sort -k1nr | head -n 1 | sed 's/[0-9]//g')
  echo $NTES$'\t'$ASES$'\t'$MAXMIN$'\t'$INST
done < asesores_comunes.txt > resumen_asesores.txt
