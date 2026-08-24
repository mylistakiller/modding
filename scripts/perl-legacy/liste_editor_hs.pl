# !/usr/bin/perl -w
# Programme Perl listant les fichiers éditeurs des unités HS
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl liste_editor_hs.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Liste les fichiers éditeurs des unités situées dans le dossier UNITS-NAME-HS\n";
my $dir = "UNITS-NAME-HS/";
my %nom_fichier = ();
my %files_editor = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-NAME-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /\*name/){
			$nom_fichier{$fich}=$ligne;
			print "$fich - $ligne\n";
		}		
		$ligne=~s/[ \*]/ /g;
		if($ligne =~ /\.col/ ){
			$files_editor{$fich}=$ligne;
			print "- $files_editor{$fich}\n";
		}
	}
	print "\n";
}

close (FILES);
closedir(REP);