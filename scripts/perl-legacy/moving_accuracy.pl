# !/usr/bin/perl -w
# Programme Perl donne aux unités RW la précision (accuracy) des unités HS
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl moving_accuracy.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Donne aux unités situées dans le dossier UNITS-RW la précision (accuracy) des unités situées dans le dossier UNITS-HS\n";
my $i=0;
my %nom_fichier = ();
my %aSNIPER = ();
my %aTRANSPIERCE = ();
my $dir = "UNITS-HS/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /soundtype ftank/ || $ligne =~ /soundtype tank/){
			$nom_fichier{$fich}=1;
		}
		if($ligne =~ /shot1_accuracy/){
			$aTRANSPIERCE{$fich}=$ligne;
		}
		if($ligne =~ /shot2_accuracy/){
			$aSNIPER{$fich}=$ligne;
		}
	}
}
my $dir = "UNITS-RW/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-RW/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	if(exists $nom_fichier{$fich}){
		$i++;
		open (new_unit, "> FUSION/$fich")or die "Impossible d'ouvrir le fichier $fich dans FUSION\n";
		while(my $ligne=<FILES>){
			chomp $ligne;
			if($ligne =~ /shot1_accuracy/){
				print new_unit "$aTRANSPIERCE{$fich}\n";
			}
			elsif($ligne =~ /shot2_accuracy/){
				print new_unit "$aSNIPER{$fich}\n";
			}
			else{
				print new_unit "$ligne\n";
			}
		}
		close(new_unit);
	}
}
close (FILES);
closedir(REP);
print "$i\n";