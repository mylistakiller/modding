# !/usr/bin/perl -w
# use strict;
# use warning;
# Ouverture des fichiers 
my $dir = "lang/";
my %nom_fichier = ();
my %nom_unites = ();
my %health = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "lang/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /soundtype tank/){
			$nom_fichier{$fich}=1;
		}
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}		
		if($ligne =~ /health/){
			my @zero = split(' ',$ligne);
			$health{$fich}=$zero[1];
		}
	}
}
foreach my $name (sort keys %nom_fichier){
	print "$name - Unit : $nom_unites{$name} - health : $health{$name}\n";
}
close (FILES);
closedir(REP);