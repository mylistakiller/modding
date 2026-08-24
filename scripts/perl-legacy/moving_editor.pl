# !/usr/bin/perl -w
# Programme Perl donne aux unités RW le blindage des unités HS
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl moving_accuracy.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Donne aux unités situées dans le dossier UNITS-RW le blindage des unités situées dans le dossier UNITS-HS\n";
my $dir = "UNITS-RW/";
my %nom_fichier = ();
my %new_name = ();
my %col = ();
# my %pck = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-RW/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /file/){
			my @zero = split(' ',$ligne);
			$nom_fichier{$fich}=$zero[1];
		}		
		$ligne=~s/[ \*]/ /g;
		if($ligne =~ /\.col/ ){
			my @zero = split(' ',$ligne);
			$files_editor{$fich}=$zero[1];
		}
	}
}
my $dir = "UNITS-NAME-HS/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "UNITS-NAME-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	if(exists $nom_fichier{$fich}){
		while(my $ligne=<FILES>){
			chomp $ligne;
			$ligne=~s/[ \*]/ /g;
			if($ligne =~ /\.col/ ){
				my @zero = split(' ',$ligne);
				$new_name{$fich}=$zero[1];
			}			
		}
		if($fich ne "" && $new_name{$fich} ne "" && $files_editor{$fich} ne ""){
			# print "main/$new_name{$fich} -> FUSION/$files_editor{$fich}\n";
			# system ("cp -R main/$new_name{$fich} FUSION/$files_editor{$fich}");
			# my @zero = split('\-.col',$new_name{$fich});
			# $new_name{$fich}=$zero[0].".col";
			# my @zero = split('\-.col',$files_editor{$fich});
			# $files_editor{$fich}=$zero[0].".col";
			print "cp -R edit/$new_name{$fich} FUSION/$files_editor{$fich}\n";
		}
	}
}
close (FILES);
closedir(REP);