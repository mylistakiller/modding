# !/usr/bin/perl -w
# use strict;
# use warning;
# Ouverture des fichiers 
my %files_used = ();
my %marked = ();
my %nom_unites = ();
my $dir = "lang/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while($fich = readdir REP) {
	open (FILES, "lang/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		$nom_fichier{$fich}=1;
		if ($ligne =~ /name / && !($ligne =~ /shortname /)){
			my @zero = split('\"',$ligne);
			$zero[1]=lc($zero[1]);
			$nom_unites{$fich}=$zero[1];
		}
		if ($ligne =~ /file /){
			my @zero = split(' ',$ligne);
			$zero[1]=lc($zero[1]);
			$files_used{$zero[1]}=1;
			# if(!exists $files_main_patch{$zero[1]} && !exists $files_main{$zero[1]}){
				# print "$nom_unites{$fich} -- $zero[1]\n";
			# }
		}
	}
}
my $dir1 = "__main.aps/";
my %files_main = ();
opendir(REP, $dir1) or die "Impossible d'ouvrir le dossier $dir";
while($fich1 = readdir REP) {
	my @zero = split('\.',$fich1);
	$zero[0]=lc($zero[0]);
	$files_main{$zero[0]}=1;
	if(!exists $files_used{$zero[0]} && !exists $marked{$zero[0]}){
		# print "main unused : $zero[0]\n";
		$marked{$zero[0]}=1;
	}
}
undef %marked;
my %files_main_patch = ();
my $dir2 = "__main_patch.aps/";
opendir(REP, $dir2) or die "Impossible d'ouvrir le dossier $dir";
while($fich1 = readdir REP) {
	my @zero = split('\.',$fich1);
	$zero[0]=lc($zero[0]);
	$files_main_patch{$zero[0]}=1;
	if(!exists $files_used{$zero[0]} && !exists $marked{$zero[0]}){
		# print "main_patch unused : $zero[0]\n";
		$marked{$zero[0]}=1;
	}	
	if(exists $files_main{$zero[0]}){
		print "already : $zero[0]\n";
	}
}
close (FILES);
closedir(REP);