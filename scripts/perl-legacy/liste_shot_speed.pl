# !/usr/bin/perl -w
# use strict;
# use warning;
# Ouverture des fichiers 
my $dir = "lang/";
my %nom_fichier = ();
my %mg = ();
my %nom_unites = ();
my %damage_shot = ();
my %range_shot = ();
my %damage_shot1 = ();
my %range_shot1 = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "lang/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /shot1_speed/){
			$nom_fichier{$fich}=1;
			my @zero = split(' ',$ligne);	
			$speed1{$fich}=$zero[1];
			$speed2{$fich}=$zero[2];
			if($zero[2] eq "" ){
				my @zero = split(',',$ligne);	
				$speed2{$fich}=$zero[1];
			}
		}
	}
}
foreach my $name (sort keys %nom_fichier){
	if($speed1{$name} != $speed2{$name}){
		print "$name - $speed1{$name} & $speed2{$name} \n";
	}
}
close (FILES);
closedir(REP);