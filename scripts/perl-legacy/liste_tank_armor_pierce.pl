# !/usr/bin/perl -w
# use strict;
# use warning;
# Ouverture des fichiers 
my $dir = "UNITS-HS/";
my %nom_fichier = ();
my %nom_unites = ();
my %pierce = ();
my %front = ();
my %side = ();
my %rear = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "UNITS-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /soundtype ftank/ || $ligne =~ /soundtype tank/ || $ligne =~ /soundtype itank/){
			$nom_fichier{$fich}=1;
		}
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}		
		if($ligne =~ /shot1_damage/){
			my @zero = split(' ',$ligne);
			# my $temp=int($zero[1]/5); # Base 4.1B
			my $temp=int($zero[1]/2.96); # 4.21
			$pierce{$fich}=$temp;
		}
		if($ligne =~ /armor PIERCE/){
			my @zero = split(' ',$ligne);
			# my $temp=int($zero[2]*1); # Base
			my $temp=int($zero[2]*2); # 4.21
			$front{$fich}=$temp;
			$temp=int($zero[4]*1);
			$side{$fich}=$temp;
			$temp=int($zero[6]*1);
			$rear{$fich}=$temp;
		}
	}
}
foreach my $name (sort keys %nom_fichier){
	if($pierce{$name} ne ""){
		# print "$nom_unites{$name} - Perce : $pierce{$name}mm\n";
	}
	# print "Unité : $nom_unites{$name} - Perce : $pierce{$name}mm -- Blindage - Avant $front{$name}mm - Flanc $side{$name}mm - Arrière $rear{$name}mm\n";
	print "$nom_unites{$name} - Avant $front{$name}mm - Flanc $side{$name}mm - Arrière $rear{$name}mm\n";
}
close (FILES);
closedir(REP);