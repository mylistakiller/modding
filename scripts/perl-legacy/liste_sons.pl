# !/usr/bin/perl -w
# use strict;
# use warning;
# Ouverture des fichiers 
my $dir = "lang/";
my $file="liste_sons.txt"; 
open (fstoplist, $file)or die "Erreur cosine_classifier.pl : Impossible d'ouvrir le fichier $file\n";
my @stoplist = <fstoplist>;
chomp(@stoplist);
close(fstoplist);
my %stopword = ();
foreach my $line (@stoplist){
	$stopword{$line}=0;
}
my %sons_par_unites = ();
my %nom_unites = ();		
my %unites_par_sons = ();
my %sons_par_fichiers = ();
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "lang/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	my %hash = ();
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /sound / || $ligne =~ /nd_/){
			my @zero = split(' ',$ligne);
			$hash{$fich}.="| $zero[0] - $zero[1] ";
			$sons_par_fichiers{$fich}.="|$zero[1]";
			if(exists $stopword{$zero[1]}){
				$stopword{$zero[1]}++;
			}
		}
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}
	}
	$sons_par_unites{$nom_unites{$fich}}=$hash{$fich};
}
foreach my $id ( keys %sons_par_fichiers){
	foreach my $id1 (split(/\|/,$sons_par_fichiers{$id})){
		if($id1 ne ""){
			# print "$id1 - $nom_unites{$id}\n";
			$unites_par_sons{$id1}.="|$nom_unites{$id}";
		}
	}
}
my $dir = "AVIA/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "AVIA/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	my %hash = ();	
	while(my $ligne=<FILES>){
		chomp $ligne;
		if ($ligne =~ /sound / || $ligne =~ /nd_/){
			my @zero = split(' ',$ligne);
			$hash{$fich}.="| $zero[0] - $zero[1] ";
			if(exists $stopword{$zero[1]}){
				$stopword{$zero[1]}++;
			}
		}
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);			
			$nom_unites{$fich}=$zero[1];
		}
	}
	$sons_par_unites{$nom_unites{$fich}}=$hash{$fich};
}
my $dir = "MISC/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "MISC/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	my %hash = ();		
	while(my $ligne=<FILES>){
		chomp $ligne;
		my @zero = split(' ',$ligne);
		if(exists $stopword{$zero[5]}){
			$stopword{$zero[5]}++;
		}		
		if(exists $stopword{$zero[6]}){
			$stopword{$zero[6]}++;
		}
	}
}
foreach my $id (keys %unites_par_sons){
	if($id ne ""){
		print "Sound : $id ";
		foreach my $id1 (split(/\|/,$unites_par_sons{$id})){
			if($id1 ne ""){
				print "- $id1";
			}
		}
		print "\n";
	}
}
foreach my $id (keys %stopword){
	if($stopword{$id}==0 && !($id =~ /\@/)  && !($id =~ /\$/)){
		# print "$id\n";
	}
}
close (FILES);
closedir(REP);