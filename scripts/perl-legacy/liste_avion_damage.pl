# !/usr/bin/perl -w
# Programme Perl listant les dommages de l'aviation
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl liste_avion_damage.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Liste les dommages des avions situés dans le dossier AVIA\n";
my $dir = "AVIA/";
my %nom_fichier = ();
my %calibre_air = ();
my %calibre_ground = ();
my %air_shot_damage = ();
my %air_shot_accuracy = ();
my %air_shot_max = ();
my %air_shot_min = ();
my %ground_shot_damage = ();
my %ground_shot_accuracy = ();
my %ground_shot_min = ();
my %ground_shot_max = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "AVIA/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /shot_air_accuracy/){
			$nom_fichier{$fich}=1;
			my @zero = split(' ',$ligne);
			$air_shot_accuracy{$fich}=$zero[1];
		}		
		if ($ligne =~ /shot_air_id/){
			my @zero = split(' ',$ligne);
			$calibre_air{$fich}=$zero[1];
		}
		if ($ligne =~ /shot_air_damage/){
			my @zero = split(' ',$ligne);
			$air_shot_damage{$fich}=$zero[1];
		}
		if ($ligne =~ /shot_air_maxdistance/){
			my @zero = split(' ',$ligne);
			$air_shot_max{$fich}=$zero[1];
		}
		if ($ligne =~ /shot_air_mindistance/){
			my @zero = split(' ',$ligne);
			$air_shot_min{$fich}=$zero[1];
		}
		
		if ($ligne =~ /shot_grn_accuracy/){
			my @zero = split(' ',$ligne);
			$ground_shot_accuracy{$fich}=$zero[1];
		}	
		if ($ligne =~ /shot_grn_id/){
			my @zero = split(' ',$ligne);
			$calibre_ground{$fich}=$zero[1];
		}		
		if ($ligne =~ /shot_grn_damage/){
			my @zero = split(' ',$ligne);
			$ground_shot_damage{$fich}=$zero[1];
		}
		if ($ligne =~ /shot_grn_maxdistance/){
			my @zero = split(' ',$ligne);
			$ground_shot_max{$fich}=$zero[1];
		}
		if ($ligne =~ /shot_grn_mindistance/){
			my @zero = split(' ',$ligne);
			$ground_shot_min{$fich}=$zero[1];
		}
	}
}
foreach my $name (sort keys %nom_fichier){
	print "$name - Calibre $calibre_ground{$name} - Precision $ground_shot_accuracy{$name} -  Dommage $ground_shot_damage{$name} - Portée min $ground_shot_min{$name} - Portée max $ground_shot_max{$name}\n";
	print "$name - Calibre $calibre_air{$name} - Precision $air_shot_accuracy{$name} -  Dommage $air_shot_damage{$name} - Portée min $air_shot_min{$name} - Portée max $air_shot_max{$name}\n";
}
close (FILES);
closedir(REP);