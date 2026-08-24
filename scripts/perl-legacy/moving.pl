# !/usr/bin/perl -w
# Programme Perl permet de corriger en masse la résistance des équipages des unités HS
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl moving.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Correcting ... \n";
print "Correction de la résistances des équipages des unités situées dans le dossier UNITS\n";
my $i=0;
my %nom_fichier = ();
my $dir = "UNITS/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		# if ($ligne =~ /soundtype ftank/ || $ligne =~ /soundtype tank/){
		if ($ligne =~ /soundtype itank/){
			$nom_fichier{$fich}=1;
			$i++;
		}
	}
	close (FILES);
	if(exists $nom_fichier{$fich}){
		open (FILES, "UNITS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
		open (new_unit, "> NEW/$fich")or die "Impossible d'ouvrir new_unit dans le dossier NEW\n";
		while(my $ligne=<FILES>){
			chomp $ligne;
			if($ligne =~ /protection TRANSPIERCE/ || $ligne =~ /protection PIERCE/ || $ligne =~ /protection PIAT/){
				my @zero = split(' ',$ligne);
				$zero[2]=int($zero[2]*1.25);
				$zero[3]=int($zero[3]*1.35);
				$zero[4]=int($zero[4]*1.25);
				$zero[5]=int($zero[5]*1.35);
				$zero[6]=int($zero[6]*1.25);
				$zero[7]=int($zero[7]*1.35);
				# ORI armor TRANSPIERCE 84 84 51 51 51 51
				# TOOMUCH protection TRANSPIERCE 130 160 80 100 100 100
				# ORI NOT protection TRANSPIERCE 67 67 41 41 41 41
				print new_unit "$zero[0] $zero[1] $zero[2] $zero[3] $zero[4] $zero[5] $zero[6] $zero[7]\n";
			}
			else{
				print new_unit "$ligne\n";
			}
		}
		close(new_unit);
		close (FILES);
	}
}
close (FILES);
closedir(REP);
print "nombre d'unités traitées : $i\n";