# !/usr/bin/perl -w
# Programme Perl permet de corriger la vitesse de rotation de la tourelle des unités HS
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
			if($ligne =~ /gunturndelay/){
				my @zero = split(' ',$ligne);
				# Malus simple
				if($zero[1]==0){
					$zero[1]=1;
				}
				else{
					$zero[1]=int($zero[1]*1.25);
				}
				$zero[2]=$zero[1];
				# Double Malus
				# if(int($zero[1])<9 && int($zero[2])<9){
					# $zero[1]=int($zero[1]*1.25);	
					# $zero[2]=int($zero[2]*1.10);				
				# }
				# else{
					# $zero[1]=int($zero[1]*1.15);	
					# $zero[2]=int($zero[2]*1.05);
				# }
				print "AV $fich $ligne\n";
				print "AP $fich $zero[0] $zero[1] $zero[2]\n";
				print new_unit "$zero[0] $zero[1] $zero[2]\n";
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