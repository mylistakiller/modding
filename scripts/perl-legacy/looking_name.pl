# !/usr/bin/perl -w
# Programme Perl cherchant les unités ayant le même nom dans HS2 et RW
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl looking_name.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Liste les unités ayant le meme nom dans UNITS-LANG-HS et UNITS_RW\n";
my $dir = "UNITS-RW/";
my %nom_fichier = ();
my %new_name = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-RW/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	my $marked=0;
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /name/ && $marked==0 && !($ligne =~ /\*name/ )){
			my @zero = split('\"',$ligne);
			$nom_fichier{$fich}=$zero[1];
			$marked=1;
		}
	}
}
my $dir = "UNITS-LANG-HS/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-LANG-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	my $marked=0;
	if(exists $nom_fichier{$fich}){
		while(my $ligne=<FILES>){
			chomp $ligne;
			if ($ligne =~ /name/ && $marked==0){
				my @zero = split('\"',$ligne);
				$new_name{$fich}=$zero[1];
				print "$fich - \"$new_name{$fich}\"\n";
				$marked=1;
			}
		}
	}
}
close (FILES);
closedir(REP);