# !/usr/bin/perl -w
# Programme Perl listant la précision (accuracy) des unités
# Date : 14 05 2014
# Author: Jean-Valère Cossu
# email: jvcossu@gmail.com
# Usage : perl liste_accuracy.pl
# use strict;
# use warning;
# Ouverture des fichiers 
print "Listing ... \n";
print "Liste l'accuracy des unités situées dans le dossier UNITS-HS\n";
my $dir = "UNITS-HS/";
my %nom_fichier = ();
my %mg = ();
my %nom_unites = ();
my %accuracy_shot = ();
my %accuracy1_shot = ();
my %accuracy_shot1 = ();
my %accuracy1_shot1 = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "UNITS-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich dans le dossier $dir\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		$nom_fichier{$fich}=1;
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}		
		if(!exists $accuracy_shot{$fich}){
			if($ligne =~ /shot_accuracy/ || $ligne =~ /shot1_accuracy/){
				my @zero = split(' ',$ligne);
				$accuracy_shot{$fich}=$zero[1];
				$accuracy1_shot{$fich}=$zero[2];
			}
		}
		else{
			if($ligne =~ /shot1_accuracy/ || $ligne =~ /shot2_accuracy/){
				my @zero = split(' ',$ligne);
				if($zero[1] =~ /,/){
					my @zero1 = split(',',$zero[1]);
					$accuracy_shot1{$fich}=$zero1[0];
					$accuracy1_shot1{$fich}=$zero1[1];
				}
			}
		}
	}
}
foreach my $name (sort keys %accuracy_shot){
	if($accuracy_shot{$name}!=$accuracy1_shot{$name}){
		print "$name - ";
		print "$nom_unites{$name} - ";
		print "$accuracy_shot{$name} -> $accuracy1_shot{$name}\n";
	}
}
foreach my $name (sort keys %accuracy_shot1){
	if($accuracy_shot1{$name}!=$accuracy1_shot1{$name}){
		print "$name - ";
		print "$nom_unites{$name} - ";
		print "$accuracy_shot1{$name} -> $accuracy1_shot1{$name}\n";
	}
	
}
close (FILES);
closedir(REP);