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
		if ($ligne =~ /seltype howitzer/ || $ligne =~ /seltype fieldgun/ || $ligne =~ /seltype spg/ || $ligne =~ /howturret/){
			$nom_fichier{$fich}=1;
		}
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}		
		if(!exists $range_shot{$fich}){
			if($ligne =~ /shot_deadzone/ || $ligne =~ /shot1_deadzone/ || $ligne =~ /shot2_deadzone/){
				my @zero = split(' ',$ligne);
				$range_shot{$fich}=$zero[1];
			}
		}
		else{
			if($ligne =~ /shot1_deadzone/ || $ligne =~ /shot2_deadzone/){
				my @zero = split(' ',$ligne);
				$range_shot1{$fich}=$zero[1];
			}
		}
		if(!exists $damage_shot{$fich}){
			if ($ligne =~ /shot_damage/ || $ligne =~ /shot1_damage/ || $ligne =~ /shot2_damage/){
				my @zero = split(' ',$ligne);
				$damage_shot{$fich}=$zero[1];
			}
		}
		else{
			if ($ligne =~ /shot1_damage/ || $ligne =~ /shot2_damage/){
				my @zero = split(' ',$ligne);
				$damage_shot1{$fich}=$zero[1];
			}
		}
		if ($ligne =~ /shot2_id man_machine/ || $ligne =~ /shot2_id 20mm_1/){
			$mg{$fich}=1;
		}
	}
}
foreach my $name (sort keys %nom_fichier){
	print "$name - ";
	print "$nom_unites{$name} - ";
	print "$damage_shot{$name} & $range_shot{$name} ";
	if(!exists $mg{$name}){
		if(!exists $damage_shot1{$name}){
			print "\n";
		}
		else{
			print "- $damage_shot1{$name} & $range_shot1{$name}\n";
		}
	}
	else{
		print "- MG \n";
	}
}
close (FILES);
closedir(REP);