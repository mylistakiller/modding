# !/usr/bin/perl -w
# Programme Perl listant les fichiers éditeurs des unités RW et supprime les fichiers rajoutés non utilisés
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl liste_editor_rw.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Liste les fichiers éditeurs des unités situées dans le dossier UNITS-RW\n";
my $dir = "UNITS-RW/";
my %used = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-RW/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		$ligne=lc($ligne);
		if ($ligne =~ /\*picture/){
			my @zero = split(' ',$ligne);	
			$used{$zero[1]}=$zero[1];
			$used{$zero[2]}=$zero[2];
		}
	}
}
my $dir = "edit/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "edit/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	$fich=lc($fich);
	if(!exists $used{$fich}){
		system ("rm edit/$fich");
	}
}
close (FILES);
closedir(REP);