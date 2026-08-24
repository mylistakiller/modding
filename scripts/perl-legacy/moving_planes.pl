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
my $i=0;
my %aprefapc = ();
my %aprefboat = ();
my %aprefbuilt = ();
my %aprefcar = ();
my %aprefcruiser = ();
my %aprefgun = ();
my %aprefheavytank = ();
my %apreflighttank = ();
my %aprefman = ();
my %aprefmedtank = ();
my %aprefsmallgear = ();
my %aprefsoft = ();
my %apreftrain = ();
my %aprefturret = ();
my %nom_fichier = ();
my %aABJECTIVE = ();
my %pABJECTIVE = ();
my %aAIR = ();
my %pAIR = ();
my %aEXPLOSIVE = ();
my %pEXPLOSIVE = ();
my %aFIRE = ();
my %pFIRE = ();
my %aMACHINE = ();
my %pMACHINE = ();
my %aMINE = ();
my %pMINE = ();
my %aPIERCE = ();
my %pPIERCE = ();
my %aSNIPER = ();
my %pSNIPER = ();
my %aTRANSPIERCE = ();
my %pTRANSPIERCE = ();
my $dir = "AVIA-HS/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "AVIA-HS/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	while(my $ligne=<FILES>){
		chomp $ligne;
		if($ligne =~ /shot_air_accuracy/){
			$nom_fichier{$fich}=1;
			$aTRANSPIERCE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_ammo/){
			$aSNIPER{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_burstreload/){
			$aMACHINE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_burstshots/){
			$aFIRE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_flyspeed/){
			$aEXPLOSIVE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_maxddir/){
			$aAIR{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_maxdistance/){
			$aABJECTIVE{$fich}=$ligne;
		}				
		elsif($ligne =~ /shot_air_mindistance/){
			$pTRANSPIERCE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_reload/){
			$pSNIPER{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_scanradius/){
			$pPIERCE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_speed/){
			$pMACHINE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_useammo/){
			$pFIRE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_accuracy/){
			$pEXPLOSIVE{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_altitude/){
			$pAIR{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_ammo/){
			$pABJECTIVE{$fich}=$ligne;
		}		
		elsif($ligne =~ /shot_grn_burstreload/){
			$aprefapc{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_burstshots/){
			$aprefboat{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_flyspeed/){
			$aprefbuilt{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_maxddir/){
			$aprefcar{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_maxdistance/){
			$aprefcruiser{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_mindistance/){
			$aprefgun{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_reload/){
			$aprefheavytank{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_scanradius/){
			$apreflighttank{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_speed/){
			$aprefman{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_grn_useammo/){
			$aprefmedtank{$fich}=$ligne;
		}
		elsif($ligne =~ /shot_air_damage/){
			$aprefsmallgear{$fich}=$ligne;
		}	
		elsif($ligne =~ /shot_grn_damage/){
			$aprefsoft{$fich}=$ligne;
		}	
		elsif($ligne =~ /scorevalue/){
			$apreftrain{$fich}=$ligne;
		}
	}
}
my $dir = "AVIA-RW/";
opendir(REP, $dir) or die "Impossible d'ouvrir le dossier $dir";
while(my $fich = readdir REP) {
	open (FILES, "AVIA-RW/".$fich)or die "Impossible d'ouvrir le fichier $fich\n";
	if(exists $nom_fichier{$fich}){
		$i++;
		open (trace, "> FUSION/$fich")or die "Erreur jaccard.pl : Impossible d'ouvrir trace\n";
		while(my $ligne=<FILES>){
			chomp $ligne;
			if($ligne =~ /shot_air_accuracy/){
				print trace "$aTRANSPIERCE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_ammo/){
				print trace "$aSNIPER{$fich}\n";
			}
			elsif($ligne =~ /shot_air_burstreload/){
				print trace "$aMACHINE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_burstshots/){
				print trace "$aFIRE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_flyspeed/){
				print trace "$aEXPLOSIVE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_maxddir/){
				print trace "$aAIR{$fich}\n";
			}
			elsif($ligne =~ /shot_air_maxdistance/){
				print trace "$aABJECTIVE{$fich}\n";
			}				
			elsif($ligne =~ /shot_air_mindistance/){
				print trace "$pTRANSPIERCE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_reload/){
				print trace "$pSNIPER{$fich}\n";
			}
			elsif($ligne =~ /shot_air_scanradius/){
				print trace "$pPIERCE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_speed/){
				print trace "$pMACHINE{$fich}\n";
			}
			elsif($ligne =~ /shot_air_useammo/){
				print trace "$pFIRE{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_accuracy/){
				print trace "$pEXPLOSIVE{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_altitude/){
				print trace "$pAIR{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_ammo/){
				print trace "$pABJECTIVE{$fich}\n";
			}		
			elsif($ligne =~ /shot_grn_burstreload/){
				print trace "$aprefapc{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_burstshots/){
				print trace "$aprefboat{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_flyspeed/){
				print trace "$aprefbuilt{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_maxddir/){
				print trace "$aprefcar{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_maxdistance/){
				print trace "$aprefcruiser{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_mindistance/){
				print trace "$aprefgun{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_reload/){
				print trace "$aprefheavytank{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_scanradius/){
				print trace "$apreflighttank{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_speed/){
				print trace "$aprefman{$fich}\n";
			}
			elsif($ligne =~ /shot_grn_useammo/){
				print trace "$aprefmedtank{$fich}\n";
			}
			elsif($ligne =~ /shot_air_damage/){
				print trace "$aprefsmallgear{$fich}\n";
			}	
			elsif($ligne =~ /shot_grn_damage/){
				print trace "$aprefsoft{$fich}\n";
			}	
			elsif($ligne =~ /scorevalue/){
				print trace "$apreftrain{$fich}\n";
			}
			else{
				print trace "$ligne\n";
			}
		}
		close(trace);
	}
}
close (FILES);
closedir(REP);
print "$i\n";